# 代码
[generate_questions.py](generate_questions.py)   生成问题，使用[medical_data.db](medical_data.db)生成问题[qa_dataset.jsonl](qa_dataset.jsonl)
[generate_dpo.py](generate_dpo.py) #根据问题，使用2个模型回答同1个问题，使用第3个模型判断这个问题的回答，输出[dpo_dataset.jsonl](dpo_dataset.jsonl)
[analyze_dpo_dataset.py](analyze_dpo_dataset.py) #分析生成的DPO数据集
filter_dpo.py # 过滤生成的DPO数据集，生成[filter_dpo_dataset.jsonl](filter_dpo_dataset.jsonl)

# 查看[dpo_dataset.jsonl](dpo_dataset.jsonl)数据集，使用rlhf-data-explorer进行查看和分析这个数据集
[main_data_api.py](main_data_api.py)

# 过滤低质量的数据
filter_dpo.py

# 表结构
sqlite数据库文件 medical_data.db
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


**先做“有可验证 Ground Truth 的问题”**，再把它包装成 **Agent（tool calling）轨迹**，最后再合成 **DPO 的 chosen/rejected**。下面给你一套可直接落地的“从疾病库+药品库自动生成问题”的方案（含 GT 生成方法、问题模板、采样策略、以及如何做 DPO 的 rejected）。
现有工具: async def query_database_by_sql(sql: str)

遵循先生成问题和GT，然后生成DPO偏好数据集

生成问题 + Ground Truth（建议产出“结构化 GT + evidence”）
1) 建议你把 GT 做成两层

structured_gt：用于程序验收（字段值、id 列表、对比结果等）

evidence：用于训练“引用证据”（字段原文或命中片段）

这样第 2 步能稳定生成“带引用”的 chosen，也能稳定做“忽略证据”的 rejected。

2) QA+GT 的统一 schema（建议）
{
  "qid": "uuid",
  "task_type": "drug_field|disease_field|drug_search_by_kw|compare_drugs|compare_diseases|unanswerable",
  "question": "...",
  "sql": ["...可能1条或多条..."],
  "tool_result": { "...原始返回(可选)..."},
  "structured_gt": { "...用于验收..." },
  "evidence": [
    {"source_table":"drugs_info","row_id":123,"field":"indication","quote":"..."},
    {"source_table":"drugs_info","row_id":456,"field":"indication","quote":"..."}
  ],
  "meta": {
    "entity": {"drug_name":"...", "disease_name":"..."},
    "difficulty": "easy|mid|hard",
    "created_at": "2026-01-28"
  }
}

3) 第 1 步推荐先做的 3 类“强 GT”任务（最稳）
A. 单表字段抽取（最干净）

药品：indication / contraindications / adverse_reactions / dosage / precautions …

疾病：clinical_manif / treatment / diagnosis / prevention …

GT 生成方式：SELECT ... FROM ... WHERE id = ? 或 WHERE name LIKE ? LIMIT 1

structured_gt：字段全文（或截断后）

evidence：同字段 quote（可直接用字段全文或截取一句）

B. 同表对比（依然强 GT）

例：对比两个药的禁忌/不良反应

structured_gt：A 字段、B 字段、差异点（差异点可以让程序用简单规则生成：例如“只在 A 出现的句子/关键词集合”）

evidence：A/B 各自引用片段

C. 关键词检索（弱一些但可验证）

例：适应症包含“支气管炎”的药 Top3

structured_gt：命中药品 id 列表 + 每个药的命中位置/片段

evidence：每个药对应的命中 quote（关键词前后各 N 字）

第 1 步的验收标准：structured_gt 能 100% 用 SQL 结果重算出来；evidence.quote 必须来自字段文本的子串（可做 contains 校验）。

---

## 4) 如何从库里自动“采样 + 生成问题”流程（推荐流水线）

### Step A：构建实体池

* 疾病池：`disease_name` 非空，且某些字段（treatment/clinical_manif）长度 > N
* 药品池：`med_name` 非空，且 indication/dosage/contraindications/adverse_reactions 非空

### Step B：模板随机化（避免模型记模板）

同一个字段至少 5–10 种问法：

* “适应症有哪些/用于什么病/可治疗什么/主要用途…”
* “禁忌/哪些情况不能用/慎用人群…”
  并加少量噪声（口语化、错别字、缩写）。

### Step C：生成 GT

* 单库：直接字段
* 跨库：LIKE/全文检索 + 证据片段抽取
* 不可答：GT = “无法从库确定 + 建议就医 + 提示查看禁忌/注意事项”

### Step D：生成 Agent 轨迹（chosen）

统一策略：**先 search，再 get，再总结**
把 tool response 的关键字段（比如 matched snippet）带回 assistant。

### Step E：生成 rejected（DPO 的负样本）

你给的格式是 `rejected_messages`（完整对话），很好。常见 rejected 生成策略：

1. **不调用工具**直接编：

   * “我觉得…” “一般来说…” 没引用
2. **调用错工具/错参数**：

   * disease 问题用 drug search；或传空参数
3. **忽略 tool 结果**：

   * tool 返回 NOT_FOUND 但仍给药名
4. **过度医疗建议**（危险）：

   * 直接给剂量/疗程/处方建议（不引用 dosage 字段）

> DPO 的价值就在于：让模型更偏好“可执行、可验证、会用工具”的行为。

---

## 5) 你这个 DPO JSON 格式建议小调整（更利于训练）

你现在是：

* `messages`：chosen 完整对话
* `rejected_messages`：rejected 完整对话
* 还分 `tools`/`rejected_tools`

更通用的做法是：

* tools 一般保持一致（减少变量）
* DPO 比较的核心是“同一上下文下最后 assistant 输出的 chosen vs rejected”
  但如果你坚持“完整对话对比”，也能做，只要你的训练脚本支持“对话级 chosen/rejected”。如果你用 ms-swift，通常是 `messages` + `rejected_response` 更常见；你可以在生成阶段同时保存两份：
* `messages`（chosen）
* `rejected_response`（rejected 的最后 assistant content）
  同时保留 `rejected_messages` 便于回放/分析。

---

## 6) 一个你场景的最小样本示例（疾病→药品，带证据）

（示例字段你替换成真实库结果）

```json
{
  "tools": [ ... ],
  "messages": [
    {"role":"user","content":"治疗“支气管炎”在你们药品库里有哪些药？请给3个，并引用每个药说明书适应症里包含“支气管炎”的原文一句。"},
    {"role":"tool_call","content":"{\"name\":\"search_drug_by_indication\",\"arguments\":{\"keyword\":\"支气管炎\",\"top_k\":3}}"},
    {"role":"tool_response","content":"{\"results\":[{\"drug_id\":\"D1\",\"med_name\":\"xxx\",\"evidence\":\"...用于支气管炎...\"},{\"drug_id\":\"D2\",\"med_name\":\"yyy\",\"evidence\":\"...支气管炎...\"},{\"drug_id\":\"D3\",\"med_name\":\"zzz\",\"evidence\":\"...支气管炎...\"}]}"},
    {"role":"assistant","content":"在药品库中适应症明确包含“支气管炎”的药有：1）xxx（D1）：“…用于支气管炎…”；2）yyy（D2）：“…支气管炎…”；3）zzz（D3）：“…支气管炎…”。如需用药请遵医嘱，并结合禁忌/注意事项。"}
  ],
  "rejected_messages": [
    {"role":"user","content":"治疗“支气管炎”在你们药品库里有哪些药？请给3个，并引用每个药说明书适应症里包含“支气管炎”的原文一句。"},
    {"role":"assistant","content":"可以吃阿司匹林、头孢和布洛芬，效果都很好。"}
  ]
}
```

GT 就是 tool_response 里的 `results`（可自动核对）。

---

## 7) 立刻可做的落地清单（不需要额外知识图谱）

1. 先做 **任务族1+2（强 GT）**：跑通 Agent + DPO pipeline
2. 再做 **任务族4+5（弱 GT，带 evidence）**：用字符串命中 + 证据片段
3. 最后加 **任务族6（安全合规）**：训练正确拒答与引用

---
