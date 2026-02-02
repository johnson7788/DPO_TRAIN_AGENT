#!/usr/bin/env python3
"""
分析 DPO 数据集
- 总样本数量
- 模型种类和赢的比例（被用作 chosen 模型的数量）
- messages 字符长度分布
"""

import json
import statistics
from collections import Counter

def analyze_dpo_dataset(file_path):
    # 读取数据集
    samples = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            samples.append(json.loads(line))
    
    print(f"=" * 60)
    print(f"DPO 数据集分析报告")
    print(f"=" * 60)
    
    # 1. 总样本数量
    print(f"\n【1. 总样本数量】")
    print(f"   总样本数: {len(samples)}")
    
    # 2. 分析 meta 中的模型种类和 chosen 比例
    print(f"\n【2. 模型种类及赢的比例 (chosen)】")
    
    # 收集所有模型
    model_chosen_count = Counter()  # 模型作为 chosen 的次数
    all_models = set()  # 所有出现的模型
    
    for sample in samples:
        metadata = sample.get('metadata', {})
        if metadata:
            # 获取所有模型
            models = metadata.get('models', {})
            all_models.update(models.keys())
            
            # 获取 chosen 模型
            chosen_model = metadata.get('chosen_model', '')
            if chosen_model:
                model_chosen_count[chosen_model] += 1
    
    print(f"   所有模型: {sorted(all_models)}")
    print(f"   发现的模型数量: {len(all_models)}")
    print(f"   模型作为 chosen 的次数统计:")
    for model, count in model_chosen_count.most_common():
        percentage = count / len(samples) * 100
        print(f"   - {model}: {count} ({percentage:.2f}%)")
    
    # 3. 任务类型分析
    print(f"\n【3. 任务类型分布】")
    task_types = Counter()
    for sample in samples:
        metadata = sample.get('metadata', {})
        if metadata:
            task_type = metadata.get('task_type', 'unknown')
            task_types[task_type] += 1
    
    for task_type, count in task_types.most_common():
        percentage = count / len(samples) * 100
        print(f"   - {task_type}: {count} ({percentage:.2f}%)")
    
    # 4. messages 字符长度分布
    print(f"\n【4. Messages 字符长度分布】")
    
    all_msg_lengths = []
    for sample in samples:
        messages = sample.get('messages', [])
        for msg in messages:
            content = msg.get('content', '')
            if isinstance(content, str):
                all_msg_lengths.append(len(content))
    
    if all_msg_lengths:
        print(f"   总 messages 数量: {len(all_msg_lengths)}")
        print(f"   字符长度统计:")
        print(f"   - 最小: {min(all_msg_lengths)}")
        print(f"   - 最大: {max(all_msg_lengths)}")
        print(f"   - 平均: {statistics.mean(all_msg_lengths):.2f}")
        print(f"   - 中位数: {statistics.median(all_msg_lengths):.2f}")
        print(f"   - 标准差: {statistics.stdev(all_msg_lengths):.2f}")
        
        # 分位数
        sorted_lengths = sorted(all_msg_lengths)
        p25 = sorted_lengths[int(len(sorted_lengths) * 0.25)]
        p50 = sorted_lengths[int(len(sorted_lengths) * 0.50)]
        p75 = sorted_lengths[int(len(sorted_lengths) * 0.75)]
        p90 = sorted_lengths[int(len(sorted_lengths) * 0.90)]
        p95 = sorted_lengths[int(len(sorted_lengths) * 0.95)]
        
        print(f"   分位数:")
        print(f"   - 25%: {p25}")
        print(f"   - 50%: {p50}")
        print(f"   - 75%: {p75}")
        print(f"   - 90%: {p90}")
        print(f"   - 95%: {p95}")
        
        # 长度区间分布
        print(f"\n   长度区间分布:")
        ranges = [
            (0, 100, "0-100"),
            (101, 500, "101-500"),
            (501, 1000, "501-1000"),
            (1001, 2000, "1001-2000"),
            (2001, 5000, "2001-5000"),
            (5001, float('inf'), "5000+"),
        ]
        for start, end, label in ranges:
            count = sum(1 for l in all_msg_lengths if start <= l <= end)
            pct = count / len(all_msg_lengths) * 100
            print(f"   - {label}: {count} ({pct:.2f}%)")
    
    # 5. 按角色统计 messages 长度
    print(f"\n【5. 按角色统计 messages 长度】")
    role_lengths = {}
    for sample in samples:
        messages = sample.get('messages', [])
        for msg in messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            if isinstance(content, str):
                if role not in role_lengths:
                    role_lengths[role] = []
                role_lengths[role].append(len(content))
    
    for role, lengths in sorted(role_lengths.items()):
        if lengths:
            print(f"   {role}:")
            print(f"   - 数量: {len(lengths)}")
            print(f"   - 平均长度: {statistics.mean(lengths):.2f}")
            print(f"   - 最小: {min(lengths)}, 最大: {max(lengths)}")
    
    print(f"\n{'=' * 60}")
    
    # 6. 额外分析: rejected 模型（通过 models 减去 chosen）
    print(f"\n【6. Rejected 模型统计】")
    model_rejected_count = Counter()
    for sample in samples:
        metadata = sample.get('metadata', {})
        if metadata:
            models = metadata.get('models', {})
            chosen_model = metadata.get('chosen_model', '')
            for model in models.keys():
                if model != chosen_model:
                    model_rejected_count[model] += 1
    
    print(f"   模型作为 rejected 的次数统计:")
    for model, count in model_rejected_count.most_common():
        percentage = count / len(samples) * 100
        print(f"   - {model}: {count} ({percentage:.2f}%)")

if __name__ == '__main__':
    analyze_dpo_dataset('dpo_dataset.jsonl')
