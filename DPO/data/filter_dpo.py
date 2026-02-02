#!/usr/bin/env python3
"""
过滤 DPO 数据集
只保留 chosen_model 为 deepseek-v3.2 的数据和数据不为空的数据，去掉”系统错误“的数据
"""

import json
import argparse


def should_filter_message(messages: list) -> tuple:
    """检查 messages 最后一条是否应该被过滤"""
    if not messages or len(messages) == 0:
        return False, None, ""

    last_msg = messages[-1]
    content = last_msg.get('content', '') if isinstance(last_msg, dict) else str(last_msg)

    if '系统错误' in content or len(content) <= 5:
        return True, 'messages', content
    return False, None, ""


def filter_dataset(input_file: str, output_file: str) -> dict:
    """过滤数据集，只保留 deepseek-v3.2 选中的数据"""
    filtered_out = []
    kept = 0
    target_model = "deepseek-v3.2"

    with open(input_file, 'r', encoding='utf-8') as f:
        with open(output_file, 'w', encoding='utf-8') as out_f:
            for i, line in enumerate(f, 1):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    metadata = data.get('metadata', {})
                    chosen_model = metadata.get('chosen_model', '')

                    if chosen_model == target_model:
                        messages = data.get('messages', [])
                        rejected_messages = data.get('rejected_messages', [])

                        should_filter, source, content = should_filter_message(messages)

                        if not should_filter:
                            should_filter, source, content = should_filter_message(rejected_messages)

                        if should_filter:
                            filtered_out.append({
                                'line': i,
                                'source': source,
                                'content': content,
                                'length': len(content)
                            })
                        else:
                            out_f.write(line)
                            kept += 1
                    else:
                        filtered_out.append({
                            'line': i,
                            'chosen_model': chosen_model
                        })

                except json.JSONDecodeError:
                    continue

    return {
        'total': kept + len(filtered_out),
        'kept': kept,
        'filtered': len(filtered_out),
        'filtered_items': filtered_out
    }


def main():
    parser = argparse.ArgumentParser(description='过滤 DPO 数据集，只保留 chosen_model 为 deepseek-v3.2 的数据')
    parser.add_argument('--input', '-i', default='dpo_dataset.jsonl', help='输入文件路径')
    parser.add_argument('--output', '-o', default='filter_dpo_dataset.jsonl', help='输出文件路径')
    args = parser.parse_args()

    result = filter_dataset(args.input, args.output)

    print(f"\n过滤结果:")
    print(f"  过滤前总行数: {result['total']}")
    print(f"  保留行数 (deepseek-v3.2): {result['kept']}")
    print(f"  过滤掉行数: {result['filtered']}")
    print(f"\n过滤掉的模型分布:")
    print("-" * 80)
    model_counts = {}
    for item in result['filtered_items']:
        model = item.get('chosen_model', 'unknown')
        model_counts[model] = model_counts.get(model, 0) + 1
    for model, count in sorted(model_counts.items(), key=lambda x: -x[1]):
        print(f"  {model}: {count} 条")
    print("-" * 80)


if __name__ == '__main__':
    main()
