# vllm推理
bash start_vllm.sh
测试不同模型，请求时使用训练前后的模型：
'metadata': {"user_data": "hello", "language": "japanese", "history": history, "model": "local_agent_model", "provider": "vllm"}
'metadata': {"user_data": "hello", "language": "japanese", "history": history, "model": "Qwen/Qwen2.5-7B-Instruct", "provider": "silicon"}

{'id': '76d0bf2e67ac4d0dbd0dd0cb9c1db7e4', 'jsonrpc': '2.0', 'result': {'artifact': {'artifactId': 'aedc8ebd-38f4-46e9-84bf-1b089ca27682', 'metadata': {'user_data': 'hello', 'language': 'japanese', 'history': [], 'model': 'local_agent_model', 'provider': 'vllm'}, 'parts': [{'kind': 'text', 'metadata': {}, 'text': '根据查询结果，药品"白葡奈氏菌片"的查询结果如下：\n\n## 查询结果\n\n### 基本信息\n**药品名称**: 白葡奈氏菌片\n**剂型**: 薄膜衣片\n**规格**: 0.3mg\n**批准文号**: 国药准字 H37023540\n**生产企业**: 齐鲁制药有限公司\n\n### 主要成分\n**主要成分**: \n- **白色葡萄球菌**\n- **奈瑟卡他球菌**\n- **枯草芽孢杆菌**\n\n### 适应症\n**适应症**: \n**慢性气管炎及喘息性气管炎**\n\n### 用法用量\n**用法**: 口服\n**用量**:\n- **预防用量**: 成人一次 1～2 片，一日 2 次\n- **治疗用量**: 成人一次 2～4 片，一日 2～3 次\n- **儿童用量**: 酌减，或遵医嘱\n\n### 注意事项\n**注意事项**:\n- **禁忌症**: 对本品过敏者禁用\n- **不良反应**: 尚未发现有关不良反应报道\n- **用药禁忌**:\n  - **禁烟、酒和辛辣等刺激性食物**\n  - **当药品性状发生改变时禁止使用**\n\n### 药理作用\n**药理作用**:\n- **增强免疫功能**:\n  - **诱生干扰素**\n  - **激活补体 C3 途径**\n  - **调动网状内皮系统机能**\n  - **增强白细胞吞噬机能**\n  - **提高机体非特异性免疫功能**\n  - **增强呼吸道粘膜特异性免疫功能**\n  \n- **镇咳作用**:\n  - **抑制咳嗽反射**\n  - **调节植物神经功能**\n  - **抑制呼吸道黏膜腺体分泌**\n  - **使痰量明显减少**\n\n### 贮藏条件\n**贮藏条件**:\n- **贮藏方式**: 密闭，在阴凉（不超过 20 ℃）干燥处保存\n- **有效期**: 36 个月\n\n## 结论\n\n根据查询结果：\n**药品"白葡奈氏菌片"的主要适应症是慢性气管炎及喘息性气管炎**。\n\n### 详细信息总结\n1. **药品名称**: 白葡奈氏菌片\n2. **批准文号**: 国药准字 H37023540\n3. **生产企业**: 齐鲁制药有限公司\n4. **主要成分**: \n   - **白色葡萄球菌**\n   - **奈瑟卡他球菌**\n   - **枯草芽孢杆菌**\n5. **适应症**: \n   - **慢性气管炎**\n   - **喘息性气管炎**\n6. **用法用量**: \n   - **预防用量**: 成人一次 1～2 片，一日 2 次\n   - **治疗用量**: 成人一次 2～4 片，一日 2～3 次\n   - **儿童用量**: 酌减，或遵医嘱\n7. **注意事项**:\n   - **禁忌症**: 对本品过敏者禁用\n   - **不良反应**: 尚未发现有关不良反应报道\n   - **用药禁忌**:\n     - **禁烟、酒和辛辣等刺激性食物**\n     - **当药品性状发生改变时禁止使用**\n8. **药理作用**:\n   - **增强免疫功能**:\n     - **诱生干扰素**\n     - **激活补体 C3 途径**\n     - **调动网状内皮系统机能**\n     - **增强白细胞吞噬机能**\n     - **提高机体非特异性免疫功能**\n     - **增强呼吸道粘膜特异性免疫功能**\n   - **镇咳作用**:\n     - **抑制咳嗽反射**\n     - **调节植物神经功能**\n     - **抑制呼吸道黏膜腺体分泌**\n     - **使痰量明显减少**\n9. **贮藏条件**:\n   - **贮藏方式**: 密闭，在阴凉（不超过 20 ℃）干燥处保存\n   - **有效期**: 36 个月\n\n## 结论\n\n**药品"白葡奈氏菌片"的主要适应症是慢性气管炎及喘息性气管炎**。\n\n## 建议\n根据查询结果：\n1. **临床应用建议**:\n   - **适应症明确**: 治疗慢性气管炎及喘息性气管炎\n   - **机制独特**: 同时具有免疫调节和镇咳作用\n2. **注意事项**:\n   - **禁忌症明确**: 对本品过敏者禁用\n   - **不良反应罕见**: 尚未发现不良反应报道\n3. **贮藏要求严格**:\n   - **阴凉干燥**: 需在阴凉干燥处保存\n   - **有效期管理**: 36个月的有效期管理\n4. **临床应用范围**:\n   - **呼吸科**: 主要应用于呼吸科\n   - **家庭保健**: 适用于慢性气管炎患者的家庭保健\n5. **研究方向**:\n   - **长期疗效观察**: 进行长期疗效观察\n   - **与其他药物联合应用**: 探讨与其他药物联合应用的可能性\n\n## 总结\n**药品"白葡奈氏菌片"的主要适应症是慢性气管炎及喘息性气管炎**，其独特的药理作用和严格的贮藏条件使其成为治疗慢性气管炎患者的理想选择。'}]}, 'contextId': '68364b71-7596-42d4-a36c-24cad45d947a', 'kind': 'artifact-update', 'taskId': 'b1348f21-f304-4415-8e8a-683aac8c7dbf'}}
{'id': '6787408ccfee446f994304d28aa8784e', 'jsonrpc': '2.0', 'result': {'artifact': {'artifactId': 'a155fb23-7cae-4c4b-8ff7-e2b4ca6ab2a9', 'metadata': {'user_data': 'hello', 'language': 'japanese', 'history': [], 'model': 'Qwen/Qwen2.5-7B-Instruct', 'provider': 'silicon'}, 'parts': [{'kind': 'text', 'metadata': {}, 'text': '药品白葡奈氏菌片可以用来治疗慢性气管炎及喘息性气管炎。'}]}, 'contextId': 'da2c796f-4db5-4480-a93a-07ba21baaf1c', 'kind': 'artifact-update', 'taskId': '8f5e04b1-8a20-43df-af91-67b001433b3a'}}


# 合并训练后的模型到local_dpo_agent
swift export \
    --adapters output/task1_2_lora/v2-20260202-134851/checkpoint-60 \
    --merge_lora true \
    --output_dir local_dpo_agent

# 进行DPO训练
分为lora微调和full全参微调
还分成问答形式的微调和Agent形式的微调

# 示例数据的处理方式:
ms-swift/swift/llm/dataset/dataset/llm.py
register_dataset(
    DatasetMeta(
        ms_dataset_id='hjh0119/shareAI-Llama3-DPO-zh-en-emoji',
        hf_dataset_id='shareAI/DPO-zh-en-emoji',
        preprocess_func=EmojiPreprocessr(columns={
            'answer_zh': 'response',
            'answer_en': 'rejected_response'
        }),
        tags=['rlhf', 'dpo']))

# 数据处理方式
## 数据的字段处理方式1
   CUDA_VISIBLE_DEVICES=0 \
   swift rlhf \
       --rlhf_type dpo \
       --model Qwen/Qwen2.5-7B-Instruct \
       --train_type lora \
       --dataset your_dataset_path \
       --columns prompt:query chosen:response reject:rejected_response
## 或者直接用标准格式
  转换为 ms-swift 标准 DPO 格式：
   {"messages": [{"role": "user", "content": "<prompt>"}], "rejected_response": "<reject>"}

  或者带 system 的格式：
   {"messages": [{"role": "system", "content": "你是个有帮助的助手"}, {"role": "user", "content": "<prompt>"}, {"role":
   "assistant", "content": "<chosen>"}], "rejected_response": "<reject>"}
  
# 对于Agent类型的数据
https://github.com/modelscope/ms-swift/blob/main/docs/source_en/Customization/Custom-dataset.md
  {
     "tools": [...],  // 工具定义
     "messages": [
       {"role": "user", "content": "现在的具体时间是多少？"},
       {"role": "tool_call", "content": "{\"name\": \"get_current_time\", \"arguments\": {}}"},
       {"role": "tool_response", "content": "{\"result\": \"21:40:12\"}"},
       {"role": "assistant", "content": "现在的具体时间是21:40:12。"}
     ],
     "rejected_messages": [  // 拒绝回复的完整对话
       {"role": "user", "content": "现在的具体时间是多少？"},
       {"role": "assistant", "content": "我不知道当前时间"}
     ],
     "rejected_tools": [...]  // 可以相同或不同的工具定义
   }

1. 字段定义和标准键
  文件: swift/llm/dataset/preprocessor/core.py:21-26
   _pair_keys = ['messages', 'images', 'videos', 'audios', 'tools', 'objects']

   standard_keys = _pair_keys + list(
       chain.from_iterable([f'{prefix}_{k}' for k in _pair_keys]
                           for prefix in ['rejected', 'positive', 'negative'])) + [
                               'rejected_response', 'label', 'channel', 'margin']

2. rejected_messages 预处理
文件: swift/llm/dataset/preprocessor/core.py:502-508
 if 'rejected_messages' in row:
     row['rejected_messages'] = MessagesPreprocessor.preprocess(
         self, {'messages': row['rejected_messages']})['messages']

3. TemplateInputs 解析
文件: swift/llm/template/template_inputs.py:283-340
- _compat_rejected_response: 处理 rejected_response → rejected_messages 转换
- from_dict: 解析 messages、rejected_messages、tools、rejected_tools

4. tools 预处理
文件: swift/llm/template/base.py:230-258
 def _preprocess_function_call(self, inputs: StdTemplateInputs) -> None:
     agent_template = self.agent_template
     if inputs.tools:
         # 解析 tools 字段
         inputs.tools = [agent_template._parse_json(tool) for tool in inputs.tools]

5. DPO RLHF 编码
文件: swift/llm/template/base.py:361-381
 def _rlhf_encode(self, inputs: TemplateInputs, check_rejected=True) -> Dict[str, Any]:
     chosen = inputs.chosen
     chosen_encoded = self._encode_truncated(chosen)
     rejected_encoded = self._encode_truncated(inputs.rejected)
     # 合并 chosen 和 rejected 的编码结果

   数据流

✦  数据集 → AutoPreprocessor
       → MessagesPreprocessor (处理 rejected_messages)
       → _preprocess_function_call (处理 tools)
       → TemplateInputs.from_dict
       → _rlhf_encode
       → _encode_truncated
       → DPOTrainer.concatenated_forward

