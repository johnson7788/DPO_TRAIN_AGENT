#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date  : 2025/12/27
# @File  : check_dpo_dataset.py
# @Desc  : 检查和统计 DPO 数据集

import json
import os
from collections import Counter


def check_dpo_dataset(file_path: str):
    """
    检查 DPO 数据集

    Args:
        file_path: 数据集文件路径
    """
    print("=" * 80)
    print(f"检查 DPO 数据集: {file_path}")
    print("=" * 80)

    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return

    # 读取数据集
    samples = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    sample = json.loads(line)
                    samples.append(sample)
                except json.JSONDecodeError as e:
                    print(f"❌ JSON 解析错误: {e}")

    print(f"\n📊 基本信息:")
    print(f"   总样本数: {len(samples)}")

    if not samples:
        print("❌ 数据集为空")
        return

    # 统计任务族
    task_families = [s['metadata']['task_family'] for s in samples]
    task_family_counts = Counter(task_families)

    print(f"\n📈 任务族分布:")
    for task_family, count in sorted(task_family_counts.items()):
        task_name = "药品问答" if task_family == 1 else "疾病问答"
        print(f"   任务族{task_family} ({task_name}): {count} 条")

    # 统计字段分布
    print(f"\n📋 字段分布:")

    # 药品字段
    drug_fields = [s['metadata']['field'] for s in samples if s['metadata']['task_family'] == 1]
    if drug_fields:
        drug_field_counts = Counter(drug_fields)
        print("   药品字段:")
        for field, count in sorted(drug_field_counts.items(), key=lambda x: -x[1]):
            print(f"     - {field}: {count} 条")

    # 疾病字段
    disease_fields = [s['metadata']['field'] for s in samples if s['metadata']['task_family'] == 2]
    if disease_fields:
        disease_field_counts = Counter(disease_fields)
        print("   疾病字段:")
        for field, count in sorted(disease_field_counts.items(), key=lambda x: -x[1]):
            print(f"     - {field}: {count} 条")

    # 检查数据完整性
    print(f"\n✅ 数据完整性检查:")

    issues = []

    for i, sample in enumerate(samples):
        # 检查必需字段
        required_fields = ['tools', 'messages', 'rejected_messages', 'metadata']
        for field in required_fields:
            if field not in sample:
                issues.append(f"样本 {i}: 缺少字段 '{field}'")

        # 检查 metadata
        if 'metadata' in sample:
            metadata = sample['metadata']
            required_metadata = ['task_family', 'field', 'ground_truth']
            for field in required_metadata:
                if field not in metadata:
                    issues.append(f"样本 {i}: metadata 缺少字段 '{field}'")

        # 检查 messages 和 rejected_messages
        if 'messages' in sample:
            if len(sample['messages']) < 2:
                issues.append(f"样本 {i}: messages 长度不足")

        if 'rejected_messages' in sample:
            if len(sample['rejected_messages']) < 2:
                issues.append(f"样本 {i}: rejected_messages 长度不足")

    if issues:
        print(f"   发现 {len(issues)} 个问题:")
        for issue in issues[:10]:  # 只显示前10个
            print(f"     ❌ {issue}")
        if len(issues) > 10:
            print(f"     ... 还有 {len(issues) - 10} 个问题")
    else:
        print("   ✅ 所有样本数据完整")

    # 显示样本示例
    print(f"\n📝 样本示例 (前2条):")

    for i in range(min(2, len(samples))):
        sample = samples[i]
        task_family = sample['metadata']['task_family']
        task_name = "药品问答" if task_family == 1 else "疾病问答"
        field = sample['metadata']['field']

        print(f"\n--- 样本 {i + 1} (任务族{task_family} - {task_name} - {field}) ---")

        # 显示 user 消息
        user_msg = sample['messages'][0]
        print(f"用户问题: {user_msg['content']}")

        # 显示 chosen 回答
        chosen_answer = [m for m in sample['messages'] if m['role'] == 'assistant'][-1]
        answer_preview = chosen_answer['content'][:100] + "..." if len(chosen_answer['content']) > 100 else chosen_answer['content']
        print(f"Chosen 回答: {answer_preview}")

        # 显示 rejected 回答
        rejected_answer = sample['rejected_messages'][-1]
        rejected_preview = rejected_answer['content'][:100] + "..." if len(rejected_answer['content']) > 100 else rejected_answer['content']
        print(f"Rejected 回答: {rejected_preview}")

        # 显示工具调用
        tool_calls = [m for m in sample['messages'] if m['role'] == 'tool_call']
        print(f"工具调用次数: {len(tool_calls)}")

    # 统计 token 长度
    print(f"\n📏 Token 长度统计 (估算):")

    token_lengths = []
    for sample in samples:
        # 估算 token 长度 (粗略按字符数/4)
        full_text = json.dumps(sample, ensure_ascii=False)
        estimated_tokens = len(full_text) // 4
        token_lengths.append(estimated_tokens)

    if token_lengths:
        import statistics
        print(f"   最小值: {min(token_lengths)} tokens")
        print(f"   最大值: {max(token_lengths)} tokens")
        print(f"   平均值: {statistics.mean(token_lengths):.0f} tokens")
        print(f"   中位数: {statistics.median(token_lengths):.0f} tokens")

    print("\n" + "=" * 80)
    print("✅ 检查完成")
    print("=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='检查 DPO 数据集')
    parser.add_argument('file', type=str, help='DPO 数据集文件路径')

    args = parser.parse_args()

    check_dpo_dataset(args.file)