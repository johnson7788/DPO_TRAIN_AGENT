#!/bin/bash

# 模型路径
MODEL_PATH="/workspace/post_train/step5_DPO/local_dpo_agent"

# 启动 vLLM 服务器
# --port 8000: 服务端口
# --served-model-name: 给模型起个简单的名字，方便客户端调用
# --dtype bfloat16: 对应训练时的精度，避免转换错误
# --trust-remote-code: 如果模型架构包含自定义代码则需要
# gpu-memory-utilization 0.6 使用多少显存，越多越快
python -m vllm.entrypoints.openai.api_server \
    --model $MODEL_PATH \
    --served-model-name local_agent_model \
    --dtype bfloat16 \
    --port 8400 \
    --trust-remote-code \
    --max-model-len 4096 \
    --enable-auto-tool-choice \
    --gpu-memory-utilization 0.8 \
    --tool-call-parser hermes