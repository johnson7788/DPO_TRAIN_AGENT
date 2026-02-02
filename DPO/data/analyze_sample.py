#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc  : 分析 DPO 样本

import json

with open('dpo_task1_2_dataset.jsonl', 'r', encoding='utf-8') as f:
    line = f.readline()
    sample = json.loads(line)

print("=" * 80)
print("📦 DPO 样本分析")
print("=" * 80)

print("\n🔧 可用工具:")
for tool in sample['tools']:
    print(f"  - {tool}")

print("\n💬 Chosen 轨迹 (正确工具调用):")
for i, msg in enumerate(sample['messages']):
    role = msg['role']
    content = msg['content']
    
    if role == 'user':
        print(f"\n  {i+1}. 👤 用户: {content}")
    elif role == 'tool_call':
        tool_data = json.loads(content)
        print(f"\n  {i+1}. 🤖 调用工具: {tool_data['name']}")
        print(f"     参数: {json.dumps(tool_data['arguments'], ensure_ascii=False)}")
    elif role == 'tool_response':
        print(f"\n  {i+1}. 📊 工具返回: (省略详细内容)")
    elif role == 'assistant':
        preview = content[:150] + "..." if len(content) > 150 else content
        print(f"\n  {i+1}. 💡 助手回答: {preview}")

print("\n\n❌ Rejected 轨迹 (错误行为):")
for i, msg in enumerate(sample['rejected_messages']):
    role = msg['role']
    content = msg['content']
    
    if role == 'user':
        print(f"\n  {i+1}. 👤 用户: {content}")
    elif role == 'assistant':
        print(f"\n  {i+1}. 💡 助手回答 (未调用工具): {content}")

print("\n\n📊 元数据:")
print(json.dumps(sample['metadata'], ensure_ascii=False, indent=2))

print("\n" + "=" * 80)
print("✅ 分析完成")
print("=" * 80)