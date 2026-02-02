#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DPO 数据集生成器

从 qa_dataset.jsonl 读取问题，调用 A2A 服务获取回答，
使用 LLM 评判生成 DPO 格式的偏好数据集。
"""
import re
import asyncio
import json
import uuid
import logging
import httpx
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from prompt import QA_prompt

from a2a.client import A2AClient
from a2a.types import (
    MessageSendParams,
    SendMessageRequest,
    SendStreamingMessageRequest,
)
from llm_invoke import get_llm_config, acompletion

import dotenv
dotenv.load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# A2A 服务配置
A2A_SERVER_URL = "http://localhost:11087"

# 工具定义（OpenAI 格式）
# 从 agent.py 中的 query_database_by_sql 转换而来
QUERY_DATABASE_TOOL = {
    "type": "function",
    "function": {
        "name": "query_database_by_sql",
        "description": "Execute SQL query to search medical database",
        "parameters": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "SQL query statement to execute"
                }
            },
            "required": ["sql"],
            "additionalProperties": False
        }
    }
}

DEFAULT_TOOLS = [QUERY_DATABASE_TOOL]


def generate_qid() -> str:
    """生成唯一问题ID"""
    return str(uuid.uuid4())


def current_date() -> str:
    """返回当前日期"""
    return datetime.now().strftime("%Y-%m-%d")

async def call_ebm_agent(user_message: str, history: list = [], language: str = "chinese", model: str = "deepseek-v3", provider: str = "ali", prompt:str = "", tools: list = []):
    """调用 ebm循证 agent 获取流式响应（包含文本和工具调用信息）
    history: 历史聊天记录
    search_result： 最近的一次搜索结果
    """
    try:
        from a2a.client import A2AClient
        from a2a.types import MessageSendParams, SendStreamingMessageRequest

        timeout = httpx.Timeout(120.0)
        async with httpx.AsyncClient(timeout=timeout) as httpx_client:
            client = await A2AClient.get_client_from_agent_card_url(
                httpx_client, A2A_SERVER_URL
            )
            request_id = uuid.uuid4().hex

            send_message_payload = {
                'message': {
                    'role': 'user',
                    'parts': [{'type': 'text', 'text': user_message}],
                    'messageId': request_id,
                    'metadata': {
                        "language": language,
                        "history": history,
                        "model": model,
                        "provider": provider,
                        "prompt": prompt,
                        "tools": tools
                    }
                }
            }

            logger.info(f"[A2A] >>> Calling search agent: {user_message}")

            streaming_request = SendStreamingMessageRequest(
                id=request_id,
                params=MessageSendParams(**send_message_payload)
            )

            stream_response = client.send_message_streaming(streaming_request)

            chunk_count = 0
            async for chunk in stream_response:
                chunk_count += 1
                chunk_data = chunk.model_dump(mode='json', exclude_none=True)

                if chunk_data.get('result', {}).get('kind') == 'status-update':
                    status = chunk_data['result'].get('status', {})

                    if 'message' in status:
                        message = status['message']
                        if 'parts' in message:
                            for part in message['parts']:
                                part_kind = part.get('kind')

                                # 1. 处理文本
                                if part_kind == 'text' and 'text' in part:
                                    yield {"type": "text", "content": part['text']}
                                    logger.info(f"[A2A] <<< Streaming text chunk: {part['text'][:30]}...")

                                # 2. 处理工具
                                elif part_kind == 'data' and 'data' in part:
                                    inner_data_list = part['data'].get('data', [])
                                    for item in inner_data_list:
                                        item_type = item.get('type')
                                        if item_type == 'function_call':
                                            yield {"type": "function_call", "content": item}
                                            logger.info(f"[A2A] <<< Function Call: {item.get('name')}")
                                        elif item_type == 'function_response':
                                            yield {"type": "function_response", "content": item}
                                            logger.info(f"[A2A] <<< Function Response: {item.get('name')}")

                elif chunk_data.get('result', {}).get('kind') == 'artifact-update':
                    continue

    except ImportError:
        logger.error("[A2A] !!! a2a module not found")
        yield {"type": "error", "content": "系统配置错误：缺少必要的库。"}
    except Exception as e:
        logger.error(f"[A2A] !!! Error: {e}", exc_info=True)
        yield {"type": "error", "content": f"系统错误：{str(e)}"}


async def process_question(question: str, question_id: str, model: str, provider: str) -> Dict[str, Any]:
    """处理单个问题，调用Agent获取回答

    Args:
        question: 问题字典，包含 id, content, category

    Returns:
        处理结果，包含 session_id, question_id 和 steps
    """
    question_content = question

    logger.info(f"开始处理问题: {question}")

    # 生成会话ID
    session_id = f"S_{uuid.uuid4().hex[:8]}"

    # 收集Agent响应的步骤
    steps = []
    step_counter = 0

    try:
        # 调用Agent（异步生成器）
        async for chunk in call_ebm_agent(question_content, history=[], language="chinese", model=model, provider=provider):
            chunk_type = chunk.get("type")
            content = chunk.get("content")

            if chunk_type == "text":
                # 文本响应
                step = {
                    "role": "assistant",
                    "content": content,
                    "tool_name": None,
                    "params": None,
                    "output": None
                }
                steps.append(step)
                logger.info(f"  [Text] {content[:30]}...")

            elif chunk_type == "function_call":
                # 工具调用
                step = {
                    "role": "tool_call",
                    "content": f"调用工具: {content.get('name', 'unknown')}",
                    "tool_name": content.get('name'),
                    "params": content.get('args'),
                    "output": None
                }
                steps.append(step)
                logger.info(f"  [Function Call] {content.get('name')}")

            elif chunk_type == "function_response":
                # 工具响应
                step = {
                    "role": "tool_result",
                    "content": f"工具响应: {content.get('name', 'unknown')}",
                    "tool_name": content.get('name'),
                    "params": None,
                    "output": content.get('response')
                }
                steps.append(step)
                logger.info(f"  [Function Response] {content.get('name')}")

            elif chunk_type == "error":
                # 错误信息
                step = {
                    "role": "assistant",
                    "content": f"错误: {content}",
                    "tool_name": None,
                    "params": None,
                    "output": None
                }
                steps.append(step)
                logger.error(f"  [Error] {content}")

            step_counter += 1

        logger.info(f"问题 [{session_id}] 处理完成，共 {len(steps)} 个步骤")

    except Exception as e:
        logger.error(f"处理问题 [{session_id}] 时出错: {e}")
        steps.append({
            "role": "assistant",
            "content": f"处理出错: {str(e)}",
            "tool_name": None,
            "params": None,
            "output": None
        })

    return {
        "session_id": session_id,
        "question_id": question_id,
        "steps": steps
    }

def merge_steps_struct(result: dict) -> dict:
    """将steps中的内容按规则合并，替换原有steps

    合并规则：
    1. 如果完全没有工具调用：所有 assistant 内容合并为最终 assistant 答案。
    2. 如果有工具调用：
        a. 最后一个工具响应 (tool_result) 之前的内容 -> thought
        b. 最后一个工具响应 (tool_result) 之后的内容 -> assistant
    3. 工具调用和工具响应保持原样
    """
    steps = result.get('steps', [])
    if not steps:
        return result

    new_steps = []
    thought_parts = []
    answer_parts = []

    # 1. 预检：检查是否存在工具调用/结果
    has_tool_use = any(step.get('role') in ['tool_call', 'tool_result'] for step in steps)

    # 2. 找到最后一个 tool_result 的索引（如果有）
    last_tool_result_index = -1
    for i, step in enumerate(steps):
        if step.get('role') == 'tool_result':
            last_tool_result_index = i

    for i, step in enumerate(steps):
        role = step.get('role')
        content = step.get('content', '') or ''

        if role == 'assistant':
            if not has_tool_use:
                # 情况 A: 完全没有工具调用，全部视为最终答案
                answer_parts.append(content)
            elif i <= last_tool_result_index:
                # 情况 B: 有工具调用，且在最后一个结果之前，视为思考过程
                thought_parts.append(content)
            else:
                # 情况 C: 有工具调用，且在最后一个结果之后，视为最终答案
                answer_parts.append(content)

        elif role == 'tool_call':
            # 遇到工具调用时，把之前的思考过程 flush 进去
            if thought_parts:
                new_steps.append({
                    "role": "thought",
                    "content": ''.join(thought_parts)
                })
                thought_parts = []
            new_steps.append(step)

        elif role == 'tool_result':
            new_steps.append(step)

        elif role == 'error':
            new_steps.append(step)

    # 3. 最后清理：将剩余的内容放入对应的角色中

    # 如果还有残留的 thought（针对有工具调用的情况）
    if thought_parts:
        new_steps.append({
            "role": "thought",
            "content": ''.join(thought_parts)
        })

    # 如果有合并好的 assistant 答案（无论有没有工具）
    if answer_parts:
        new_steps.append({
            "role": "assistant",
            "content": ''.join(answer_parts)
        })

    result['steps'] = new_steps

    return result


async def evaluate_answers(
    question: str,
    answer1: str,
    answer2: str,
    ground_truth: str
) -> Tuple[int, str]:
    """
    使用 LLM 评判两个回答哪个更好

    Args:
        question: 用户问题
        answer1: 回答1
        answer2: 回答2
        ground_truth: 标准答案

    Returns:
        Tuple[最佳回答索引(0或1), 评判理由]
    """
    provider = "deepseek"
    model = "deepseek-chat"

    config = get_llm_config(provider, model)

    eval_prompt = f"""你是一个医疗问答质量评估专家。请对比以下两个回答的质量，选择更好的一个。

用户问题：{question}

标准答案（参考）：{ground_truth}

回答0：
{answer1}

回答1：
{answer2}

评估标准：
1. 准确性：回答是否与标准答案一致
2. 完整性：回答是否覆盖了问题的所有要点
3. 工具使用：是否正确调用了数据库查询工具
4. 引用规范：是否正确引用了数据来源

请直接输出编号（0 或 1），不要输出其他内容。
0 表示回答0更好，1 表示回答1更好。
如果两个回答都不好，选择相对更好的一个。
"""

    try:
        resp = await acompletion(
            **config,
            messages=[
                {"role": "system", "content": "你是一个公正的评估专家，直接输出数字编号。"},
                {"role": "user", "content": eval_prompt}
            ],
            temperature=0.1,
        )

        response = resp["choices"][0]["message"]["content"].strip()

        # 解析结果
        if "0" in response and "1" not in response:
            best_idx = 0
        elif "1" in response:
            best_idx = 1
        else:
            # 默认选择回答1
            best_idx = 0
            logger.warning(f"无法解析评判结果: {response}，默认选择回答1")

        logger.info(f"评判结果: 选择回答{best_idx + 1}")
        return best_idx, response

    except Exception as e:
        logger.error(f"评判失败: {e}")
        return 0, f"评判失败: {e}"

def build_messages_from_steps(steps: list, question: str) -> list:
    """根据步骤构建 DPO 格式的消息列表

    格式要求：
    - 第一条必须是 user 的原始问题
    - tool_call 的 content 必须是 JSON: {"name": "...", "arguments": {...}}
    - tool_response 的 content 必须是 JSON: {"result": "..."}
    - assistant 是最终回答
    """
    messages = []
    messages.append({"role": "system", "content": QA_prompt})
    # 1. 添加用户问题
    messages.append({"role": "user", "content": question})

    # 2. 构建中间步骤
    for step in steps:
        role = step.get('role')
        if role == 'tool_call':
            # 工具调用：content 应该是 JSON 格式
            tool_name = step.get('tool_name', '')
            params = step.get('params', {})
            content = json.dumps({"name": tool_name, "arguments": params}, ensure_ascii=False)
            messages.append({"role": "tool_call", "content": content})

        elif role == 'tool_result':
            # 工具响应：content 应该是 JSON 格式
            output = step.get('output', '')
            content = json.dumps({"result": output}, ensure_ascii=False)
            messages.append({"role": "tool_response", "content": content})

        elif role == 'assistant':
            # 最终回答
            content = step.get('content', '')
            messages.append({"role": "assistant", "content": content})

    return messages


async def generate_dpo_sample(
    httpx_client: httpx.AsyncClient,
    qa_sample: Dict[str, Any],
    model1,
    model2,
    provider1,
    provider2,
    max_retry: int = 3,
) -> Optional[Dict[str, Any]]:
    """
    生成单个 DPO 样本

    Args:
        httpx_client: httpx 异步客户端
        qa_sample: QA 样本
        max_retry: 最大重试次数

    Returns:
        DPO 样本或 None
    """
    question = qa_sample.get("question", "")
    qid = qa_sample.get("qid", "")
    ground_truth = qa_sample.get("ground_truth", "")
    task_type = qa_sample.get("task_type", "unknown")
    meta = qa_sample.get("meta", {})

    if not question or not ground_truth:
        logger.warning(f"跳过无效样本: 缺少 question 或 ground_truth")
        return None

    # 调用 A2A 服务获取2个回答
    messages1 = []
    messages2 = []
    answer1 = ''
    answer2 = ''

    for attempt in range(max_retry):
        try:
            # 第一次调用
            result1 = await process_question(question, question_id=qid,model=model1, provider=provider1)
            merged_result1 = merge_steps_struct(result1)

            # 提取最终回答
            for step in reversed(merged_result1.get('steps', [])):
                if step.get('role') == 'assistant':
                    answer1 = step.get('content', '')
                    break

            if not answer1:
                logger.warning(f"第1次调用失败: answer1 为空")
                await asyncio.sleep(1)
                continue

            # 构建消息
            messages1 = build_messages_from_steps(merged_result1.get('steps', []), question)

            # 第二次调用
            result2 = await process_question(question, question_id=qid,model=model2, provider=provider2)
            merged_result2 = merge_steps_struct(result2)

            # 提取最终回答
            for step in reversed(merged_result2.get('steps', [])):
                if step.get('role') == 'assistant':
                    answer2 = step.get('content', '')
                    break

            if not answer2:
                logger.warning(f"第2次调用失败: answer2 为空")
                await asyncio.sleep(1)
                continue

            # 构建消息
            messages2 = build_messages_from_steps(merged_result2.get('steps', []), question)

            # 如果两个回答相同，重新调用
            if answer1.strip() == answer2.strip():
                logger.info(f"两次回答相同，重新调用")
                await asyncio.sleep(1)
                continue

            break

        except Exception as e:
            logger.error(f"调用失败 (尝试 {attempt + 1}/{max_retry}): {e}")
            await asyncio.sleep(1)
    else:
        logger.error(f"达到最大重试次数，跳过该样本")
        return None

    if not messages1 or not messages2:
        logger.warning(f"获取回答失败")
        return None

    # 评判哪个回答更好
    best_idx, eval_reason = await evaluate_answers(
        question,
        answer1,
        answer2,
        ground_truth
    )

    # 构建 chosen 和 rejected
    if best_idx == 0:
        chosen_messages = messages1
        rejected_messages = messages2
        chosen_model = model1
    else:
        chosen_messages = messages2
        rejected_messages = messages1
        chosen_model = model2
    # 构建 DPO 样本
    dpo_sample = {
        "tools": DEFAULT_TOOLS,
        "messages": chosen_messages,
        "rejected_messages": rejected_messages,
        "metadata": {
            "qid": generate_qid(),
            "original_qid": qa_sample.get("qid", ""),
            "task_type": task_type,
            "question": question,
            "ground_truth": ground_truth,
            "chosen_model": chosen_model,
            "models": {model1: model1, model2: model2},
            "created_at": current_date()
        }
    }

    return dpo_sample


async def generate_dpo_dataset(
    input_file: str = "qa_dataset.jsonl",
    output_file: str = "dpo_dataset.jsonl",
    max_samples: int = 1000,
    start_idx: int = 0,
    max_retry: int = 3
) -> int:
    """
    生成 DPO 数据集

    Args:
        input_file: 输入 QA 数据集文件
        output_file: 输出 DPO 数据集文件
        max_samples: 最大样本数
        start_idx: 起始索引
        max_retry: 最大重试次数

    Returns:
        成功生成的样本数
    """
    # 读取 QA 数据集
    logger.info(f"读取 QA 数据集: {input_file}")

    qa_samples = []
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    sample = json.loads(line)
                    qa_samples.append(sample)
                except json.JSONDecodeError as e:
                    logger.error(f"JSON 解析错误: {e}")

    logger.info(f"共读取 {len(qa_samples)} 条 QA 样本")

    # 切片需要处理的数据
    qa_samples = qa_samples[start_idx:]
    logger.info(f"从索引 {start_idx} 开始，处理 {len(qa_samples)} 条样本")

    # 创建 httpx 客户端
    timeout = httpx.Timeout(200.0)
    async with httpx.AsyncClient(timeout=timeout) as httpx_client:
        saved_count = 0

        # 打开输出文件
        with open(output_file, 'a+', encoding='utf-8') as f:
            for i, qa_sample in enumerate(qa_samples):
                if saved_count >= max_samples:
                    logger.info(f"已达到最大样本数 {max_samples}")
                    break

                logger.info(f"处理样本 {i + 1}/{len(qa_samples)}")

                # 生成 DPO 样本
                dpo_sample = await generate_dpo_sample(
                    httpx_client,
                    qa_sample,
                    max_retry=max_retry,
                    model1 = MODEL1,
                    model2 = MODEL2,
                    provider1=MODEL_PROVIDER1,
                    provider2=MODEL_PROVIDER2
                )

                if dpo_sample:
                    # 保存到文件
                    f.write(json.dumps(dpo_sample, ensure_ascii=False) + "\n")
                    saved_count += 1
                    logger.info(f"已保存 {saved_count} 条 DPO 样本")
                else:
                    logger.warning(f"生成 DPO 样本失败")

                # 避免请求过快
                await asyncio.sleep(0.5)

    logger.info(f"\nDPO 数据集已保存到: {output_file}，共 {saved_count} 条")
    return saved_count


async def main():
    """主函数"""
    print("=" * 60)
    print("开始生成 DPO 数据集...")
    print("=" * 60)

    # 生成 DPO 数据集
    saved_count = await generate_dpo_dataset(
        input_file="qa_dataset.jsonl",      # 输入文件
        output_file="dpo_dataset.jsonl",    # 输出文件
        max_samples=1000,                    # 最大样本数
        start_idx=354,                         # 起始索引
        max_retry=3                          # 最大重试次数
    )

    print(f"\n完成！共生成 {saved_count} 条 DPO 数据")


if __name__ == "__main__":
    MODEL_PROVIDER1 = "ali"
    MODEL1 = "deepseek-v3.2"
    # MODEL_PROVIDER2 = "ali"
    # MODEL2 = "qwen-turbo-latest"
    # MODEL_PROVIDER2 = "openai"
    # MODEL2 = "gpt5.1"
    MODEL_PROVIDER2 = "silicon"
    MODEL2 = "Qwen/Qwen2.5-7B-Instruct"
    asyncio.run(main())