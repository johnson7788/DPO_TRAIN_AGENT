import os
import random

from google.adk.agents import Agent
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.tools.tool_context import ToolContext
from google.adk.agents.invocation_context import InvocationContext
from google.adk.tools import BaseTool
from typing import Dict, List, Any, AsyncGenerator, Optional, Union
from create_model import create_model
from google.adk.planners import BuiltInPlanner
from google.genai import types
from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools import FunctionTool
from tools import query_database_by_sql
from dotenv import load_dotenv
import prompt
import contextvars
load_dotenv()

current_model_config = contextvars.ContextVar("current_model_config", default=None)

# 2. 模型缓存，避免重复创建相同的模型实例导致开销过大
_MODEL_CACHE = {}

query_database_by_sql = FunctionTool(query_database_by_sql)

TOOL_REGISTRY = {
    "query_database_by_sql": query_database_by_sql,
}
DEFAULT_TOOLS = [query_database_by_sql]

class DynamicSearchToolset(BaseToolset):
    def __init__(self, default_tools: Optional[List[str]] = None):
        # default：如果 metadata 没给 tools，就使用默认值
        self.default_tools = default_tools or DEFAULT_TOOLS
        self.tool_name_prefix = ""  # 添加这一行来解决错误

    async def get_tools(self, readonly_context=None) -> list:
        st = getattr(readonly_context, "state", {}) if readonly_context else {}
        metadata = st.get("metadata") or {}

        requested = metadata.get("tools")  # 期望是 list[str]
        if isinstance(requested, str):
            requested = [requested]
        if not requested:
            requested = self.default_tools

        tools = []
        for name in requested:
            t = TOOL_REGISTRY.get(name)
            if t is not None:
                tools.append(t)

        # 兜底：避免出现“无工具可用”
        if not tools:
            tools = DEFAULT_TOOLS

        print(f"[DynamicSearchToolset] expose tools: {[t.name for t in tools]}")
        return tools

    async def close(self) -> None:
        return

def get_or_create_dynamic_model(model_name: str, provider: str):
    cache_key = f"{provider}:{model_name}"
    if cache_key not in _MODEL_CACHE:
        print(f"--- 正在初始化新模型实例: {cache_key} ---")
        _MODEL_CACHE[cache_key] = create_model(model=model_name, provider=provider)
    return _MODEL_CACHE[cache_key]

def before_model_callback(callback_context: CallbackContext, llm_request: LlmRequest) -> Optional[LlmResponse]:
    # 1. 检查用户输入
    agent_name = callback_context.agent_name
    history_length = len(llm_request.contents)
    metadata = callback_context.state.get("metadata")
    print(f"调用了{agent_name}模型前的callback, 现在Agent共有{history_length}条历史记录,metadata数据为：{metadata}")
    #清空contents,不需要上一步的拆分topic的记录, 不能在这里清理，否则，每次调用工具都会清除记忆，白操作了
    # llm_request.contents.clear()
    # 返回 None，继续调用 LLM
    return None
def after_model_callback(callback_context: CallbackContext, llm_response: LlmResponse) -> Optional[LlmResponse]:
    # 1. 检查用户输入，注意如果是llm的stream模式，那么response_data的结果是一个token的结果，还有可能是工具的调用
    agent_name = callback_context.agent_name
    response_parts = llm_response.content.parts
    part_texts =[]
    for one_part in response_parts:
        part_text = one_part.text
        if part_text is not None:
            part_texts.append(part_text)
    part_text_content = "\n".join(part_texts)
    metadata = callback_context.state.get("metadata")
    print(f"调用了{agent_name}模型后的callback, 这次模型回复{response_parts}条信息,metadata数据为：{metadata},回复内容是: {part_text_content}")
    #清空contents,不需要上一步的拆分topic的记录, 不能在这里清理，否则，每次调用工具都会清除记忆，白操作了
    # llm_request.contents.clear()
    # 返回 None，继续调用 LLM
    return None
def before_tool_callback(tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext) -> Optional[ToolContext]:
    """
    在工具调用前检查搜索计数，如果超过限制则跳过工具调用。
    """
    search_count = tool_context.state.get("search_count", 0)
    print(f"在调用工具 {tool.name} 之前，当前搜索次数为: {search_count}")
    if search_count >= 1:
        print(f"搜索次数已达到上限 (1次)，应该跳过工具 {tool.name} 的调用，现在不知道如何限制。")
    return None

def after_tool_callback(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext, tool_response: Dict
) -> Optional[Dict]:

  tool_name = tool.name
  print(f"调用了{tool_name}工具后的callback, tool_response数据为：{tool_response}")
  tool_context.state["search_count"] = tool_context.state.get("search_count", 0) + 1
  print(f"调用了{tool_name}工具后的callback, tool_response数据为：{tool_response}, 当前搜索次数: {tool_context.state['search_count']}")
  return None

def before_agent_callback(callback_context: CallbackContext):
    # 初始化只做一次
    state = callback_context.state
    state["search_dbs"] = []
    metadata = state.get("metadata") or {}
    # 方便工具回调记录来源
    state["search_dbs_allowed"] = metadata.get("tools") or DEFAULT_TOOLS
    # 限制最多使用的工具的搜索次数，为1次就行了，超过1次就不再搜索
    state["search_count"] = 0
    return None

# 循证智能体
class EBMAgent(LlmAgent):
    def __init__(self, **kwargs):
        super().__init__(
            name="EBMAgent",
            model=create_model(model=os.environ["LLM_MODEL"], provider=os.environ["MODEL_PROVIDER"]),
            description="循证Agent",
            instruction=self._get_dynamic_instruction,
            before_agent_callback=before_agent_callback,
            # after_model_callback=after_model_callback,
            after_tool_callback=after_tool_callback,
            before_tool_callback=before_tool_callback,
            tools=[DynamicSearchToolset()],
            # planner=BuiltInPlanner(
            #     thinking_config=types.ThinkingConfig(
            #         include_thoughts=True,
            #         thinking_budget=2048,
            #     )),
            **kwargs
        )

    @property
    def canonical_model(self):
        config = current_model_config.get()

        # 如果上下文中指定了模型，则返回动态模型
        model = None
        provider = None
        if config:
            model = config.get("model")
            provider = config.get("provider")
        if not model:
            model = os.environ["LLM_MODEL"]
        if not provider:
            provider = os.environ["MODEL_PROVIDER"]
        try:
            return get_or_create_dynamic_model(
                model_name=model,
                provider=provider
            )
        except Exception as e:
            print(f"动态加载模型失败，回退到默认模型: {e}")
    def _get_user_content_from_context(self, callback_context: CallbackContext) -> str | None:
        """
        获取用户的输入
        """
        # 1) 通过回调上下文的 user_content（如果该属性存在）
        user_content = getattr(callback_context, "user_content", None)
        if user_content and getattr(user_content, "parts", None):
            for part in user_content.parts:
                text = getattr(part, "text", None)
                if text:
                    return text
        return None

    def _get_dynamic_instruction(self, ctx: InvocationContext) -> str:
        """动态整合所有研究发现并生成指令"""
        # 从metadata中获取language和prompt
        metadata = ctx.state.get("metadata", {})
        language = metadata.get("language", "chinese")  # 默认中文
        # 优先使用metadata中传入的prompt，否则使用默认的prompt
        custom_prompt = metadata.get("prompt")
        if custom_prompt:
            return custom_prompt
        # 根据不同的情况选择不同的prompt
        user_input = self._get_user_content_from_context(ctx)
        prompt_instruction = prompt.QA_prompt
        return prompt_instruction

root_agent = EBMAgent()
