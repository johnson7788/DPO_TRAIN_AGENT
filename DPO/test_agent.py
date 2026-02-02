import os
import sys
import torch
import re
import json
from typing import Dict, Any, List
from swift.llm import (
    get_model_tokenizer,
    get_template,
    infer,
    InferArguments
)
import asyncio
from swift.tuners import Swift
from swift.llm.infer.protocol import InferRequest, RequestConfig
from swift.llm.infer.infer import SwiftInfer
from data.tools import query_database_by_sql
# ================= 配置区 =================
# 1. 您的 LoRA 权重路径 (容器内的实际路径)
ckpt_dir = 'output/task1_2_lora/v0-20260202-113433/checkpoint-50'

# 2. 基础模型 (必须和训练时一致)
base_model_type = "Qwen/Qwen2.5-7B-Instruct"

# ==========================================

print(f"🚀 正在加载模型: {base_model_type} + LoRA: {ckpt_dir}")

# 1. 定义工具，使用query_database_by_sql
tools = [
    {
        "type": "function",
        "function": {
            "name": "query_database_by_sql",
            "description": "根据sql查询数据库",
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "SQL查询语句"}
                },
                "required": ["sql"]
            }
        }
    }
]

# 2. 创建推理引擎（只加载一次模型）
infer_args = InferArguments(
    model=base_model_type,
    adapters=[ckpt_dir],
    template='qwen',
)

infer_engine = SwiftInfer(infer_args)

# 6. 工具执行函数
async def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """执行工具调用"""
    try:
        if tool_name == "query_database_by_sql":
            sq = arguments.get("sq", "")
            results = await query_database_by_sql(sq)
            if not results:
                return "未找到相关结果"
            # 只返回前3个结果，避免token过多
            return json.dumps(results[:10], ensure_ascii=False, indent=2)
        else:
            return f"未知的工具: {tool_name}"

    except Exception as e:
        return f"工具执行出错: {str(e)}"

# 7. 解析工具调用
def parse_tool_calls(response: str) -> List[Dict[str, Any]]:
    """从响应中解析工具调用"""
    tool_calls = []

    # 查找包含 "name" 和 "arguments" 的 JSON 对象
    # 使用更灵活的匹配方式
    try:
        # 先找到所有的 { 开始位置
        start_positions = [m.start() for m in re.finditer(r'\{', response)]

        for start in start_positions:
            try:
                # 从这个位置开始尝试解析 JSON
                # 向后找到匹配的 }
                brace_count = 0
                i = start
                while i < len(response):
                    if response[i] == '{':
                        brace_count += 1
                    elif response[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            # 找到完整的 JSON 对象
                            json_str = response[start:i+1]
                            try:
                                tool_call = json.loads(json_str)
                                if "name" in tool_call and "arguments" in tool_call:
                                    tool_calls.append(tool_call)
                            except json.JSONDecodeError:
                                pass
                            break
                    i += 1
            except Exception:
                continue

    except Exception as e:
        print(f"解析工具调用时出错: {e}")

    return tool_calls

async def main():
    # 8. 测试循环
    print("\n🤖 Agent 测试启动！请输入问题 (输入 q 退出)")
    SYSTEM_PROMPT = """按需使用sql进行query_database_by_sql执行查询，然后回答用户的问题。
    表结构如下:
    # drugs_info药品表
    [
        'id', 'med_name', 'med_name_initial', 'med_barcode', 'med_approval',
        'component', 'form', 'dosage', 'indication', 'adverse_reactions',
        'contraindications', 'precautions', 'company_name', 'description',
        'mechanism_action', 'cate_name', 'drug_interactions', 'storage',
        'pack', 'period', 'approve_code', 'status', 'created_at'
    ]

    # disease疾病表
    [
        'id', 'disease_name', 'overview', 'clinical_manif', 'complication',
        'epidemiology', 'examination', 'treatment', 'cause', 'diagnosis',
        'differ_diag', 'prevention', 'prognosis','create_at', 'update_at'
    ]
    """

    while True:
        query = input("\n👤 用户: ")
        if query.strip().lower() == 'q':
            break

        # ✅ 每次都以 System Prompt 开头
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # 添加用户消息
        messages.append({"role": "user", "content": query})

        # 构造请求配置
        request_config = RequestConfig(
            max_tokens=2048,
            temperature=0.7,
            top_p=0.9
        )

        # 执行推理（支持多轮工具调用）
        try:
            max_rounds = 5  # 最多5轮对话，防止无限循环
            round_count = 0

            while round_count < max_rounds:
                request = InferRequest(
                    messages=messages,
                    tools=tools
                )

                response = infer_engine.infer_single(request, request_config)
                print(f"🤖 模型回复:\n{response}")

                # 解析工具调用
                tool_calls = parse_tool_calls(response)

                if tool_calls:
                    print(f"\n🔧 检测到 {len(tool_calls)} 个工具调用:")

                    for tool_call in tool_calls:
                        tool_name = tool_call["name"]
                        arguments = tool_call["arguments"]

                        print(f"   - {tool_name}: {arguments}")

                        # 执行工具
                        tool_result = await execute_tool(tool_name, arguments)
                        print(f"   ↳ 工具结果: {tool_result[:200]}...")

                        # 添加工具调用和结果到消息历史
                        messages.append({
                            "role": "tool_call",
                            "content": json.dumps(tool_call, ensure_ascii=False)
                        })
                        messages.append({
                            "role": "tool_response",
                            "content": tool_result
                        })

                    # 继续下一轮对话
                    round_count += 1
                    print(f"\n🔄 第 {round_count} 轮对话...")
                else:
                    # 没有工具调用，结束对话
                    messages.append({"role": "assistant", "content": response})
                    print("\n✅ 对话完成")
                    break

            if round_count >= max_rounds:
                print(f"\n⚠️  达到最大轮数 {max_rounds}，停止对话")

        except Exception as e:
            print(f"❌ 推理出错: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())