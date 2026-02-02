#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date  : 2026/1/14 19:59
# @File  : llm_invoke.py
# @Author: johnson
# @Contact : github: johnson7788
# @Desc  :
import os
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from litellm import completion
from litellm import acompletion
import dotenv
dotenv.load_dotenv()
logging.basicConfig(
    handlers=[
        logging.StreamHandler()
    ],
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

def get_llm_config(provider: str, model: str) -> Dict[str, Any]:
    print(f"正在配置模型, Provider: {provider}, Model: {model}")
    config: Dict[str, Any] = {}

    if provider == "openai":
        assert os.environ.get("OPENAI_API_KEY"), "OPENAI_API_KEY is not set"
        if not model.startswith("openai/"):
            model = "openai/" + model
        config = {
            "model": model,
            "api_key": os.environ.get("OPENAI_API_KEY"),
            "api_base": "https://api.openai.com/v1"
        }

    elif provider == "deepseek":
        assert os.environ.get("DEEPSEEK_API_KEY"), "DEEPSEEK_API_KEY is not set"
        if not model.startswith("openai/"):
            model = "openai/" + model
        config = {
            "model": model,
            "api_key": os.environ.get("DEEPSEEK_API_KEY"),
            "api_base": "https://api.deepseek.com"
        }
    elif provider == "baichuan":
        assert os.environ.get("BAICHUAN_API_KEY"), "BAICHUAN_API_KEY is not set"
        if not model.startswith("openai/"):
            model = "openai/" + model
        config = {
            "model": model,
            "api_key": os.environ.get("BAICHUAN_API_KEY"),
            "api_base": "https://api.baichuan-ai.com/v1"
        }
    elif provider == "claude":
        # Claude 模型需要使用 LiteLlm，并遵循 LiteLLM 的模型命名规范
        assert os.environ.get("CLAUDE_API_KEY"), "CLAUDE_API_KEY is not set"
        # 正确的做法是使用 "claude/" 前缀
        if not model.startswith("anthropic/"):
            model = "anthropic/" + model
        config = {
            "model": model,
            "api_key": os.environ.get("CLAUDE_API_KEY"),
            "api_base": "https://api.anthropic.com/v1"
        }
    elif provider == "ali":
        assert os.environ.get("ALI_API_KEY"), "ALI_API_KEY is not set"
        if not model.startswith("openai/"):
            model = "openai/" + model
        config = {
            "model": model,
            "api_key": os.environ.get("ALI_API_KEY"),
            "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1"
        }

    elif provider == "silicon":
        assert os.environ.get("SILICON_API_KEY"), "SILICON_API_KEY is not set"
        if not model.startswith("openai/"):
            model = "openai/" + model
        config = {
            "model": model,
            "api_key": os.environ.get("SILICON_API_KEY"),
            "api_base": "https://api.siliconflow.cn/v1"
        }

    elif provider == "doubao":
        assert os.environ.get("DOUBAO_API_KEY"), "DOUBAO_API_KEY is not set"
        if not model.startswith("openai/"):
            model = "openai/" + model
        config = {
            "model": model,
            "api_key": os.environ.get("DOUBAO_API_KEY"),
            "api_base": "https://ark.cn-beijing.volces.com/api/v3"
        }

    elif provider == "vllm":
        assert os.environ.get("VLLM_API_KEY"), "VLLM_API_KEY is not set"
        assert os.environ.get("VLLM_API_URL"), "VLLM_API_URL is not set"
        if not model.startswith("openai/"):
            model = "openai/" + model
        config = {
            "model": model,
            "api_key": os.environ.get("VLLM_API_KEY"),
            "api_base": os.environ.get("VLLM_API_URL")
        }

    else:
        raise ValueError(f"Unsupported provider: {provider}")

    return config

async def generate_answer(
    question: str, evidence: List[Dict[str, Any]] = None
) -> tuple:
    """
    根据提供的问题和参考资料，生成自然语言回答

    Args:
        question: 用户问题
        evidence: 参考资料列表，每个元素包含 source_table, row_id, field, quote

    Returns:
        tuple: (成功标志, 回答内容或错误信息)
    """
    provider = os.environ.get("MODEL_PROVIDER", "deepseek")
    model = os.environ.get("LLM_MODEL", "deepseek-chat")

    config = get_llm_config(provider, model)

    # 构建参考资料内容
    evidence_content = ""
    if evidence:
        for i, ev in enumerate(evidence, 1):
            field = ev.get("field", "")
            quote = ev.get("quote", "")
            evidence_content += f"【参考资料 {i}】\n"
            evidence_content += f"字段: {field}\n"
            evidence_content += f"内容: {quote}\n\n"

    prompt = f"""你是一名医疗知识助手。
请根据以下参考资料，回答用户的问题。

参考资料：
{evidence_content}

用户问题：{question}

请给出回答："""
    logger.info(f"generate_evidence_answer LLM prompt: {prompt}")
    try:
        # 调用 LLM
        resp = await acompletion(
            **config,
            messages=[
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": "请回答以上问题。"
                }
            ],
            temperature=0.7,
        )
        response = resp["choices"][0]["message"]["content"].strip()
        return True, response
    except Exception as e:
        return False, f"解析 LLM 返回结果失败: {e}"

if __name__ == '__main__':
    # 测试
    test_question = "什么是肺癌？"

    # 简单测试 generate_answer 函数
    success, result = asyncio.run(generate_answer(test_question))
    if success:
        print(f"回答: {result}")
    else:
        print(f"错误: {result}")
