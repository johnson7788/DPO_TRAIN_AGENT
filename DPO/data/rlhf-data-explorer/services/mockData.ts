import { DataItem } from '../types';

export const SAMPLE_DATA: DataItem = {
  tools: [
    {
      type: "function",
      function: {
        name: "query_database_by_sql",
        description: "Execute SQL query to search medical database",
        parameters: {
          type: "object",
          properties: {
            sql: {
              type: "string",
              description: "SQL query statement to execute"
            }
          },
          required: ["sql"],
          additionalProperties: false
        }
      }
    }
  ],
  messages: [
    {
      role: "system",
      content: "\n按需使用sql进行execute_sql_query执行查询，然后回答用户的问题。\n表结构如下:\n# drugs_info药品表\n[\n    'id', 'med_name', 'med_name_initial', 'med_barcode', 'med_approval',\n    'component', 'form', 'dosage', 'indication', 'adverse_reactions',\n    'contraindications', 'precautions', 'company_name', 'description',\n    'mechanism_action', 'cate_name', 'drug_interactions', 'storage',\n    'pack', 'period', 'approve_code', 'status', 'created_at'\n]\n\n# disease疾病表\n[\n    'id', 'disease_name', 'overview', 'clinical_manif', 'complication',\n    'epidemiology', 'examination', 'treatment', 'cause', 'diagnosis',\n    'differ_diag', 'prevention', 'prognosis','create_at', 'update_at'\n]\n"
    },
    {
      role: "user",
      content: "药品开胸顺气丸的可以用来治什么？"
    },
    {
      role: "tool_call",
      content: "{\"name\": \"query_database_by_sql\", \"arguments\": {\"sql\": \"SELECT med_name, indication FROM drugs_info WHERE med_name LIKE '%开胸顺气丸%' OR med_name_initial LIKE '%开胸顺气丸%'\"}}"
    },
    {
      role: "tool_response",
      content: "{\"result\": {\"status\": \"success\", \"records\": [{\"med_name\": \"开胸顺气丸\", \"indication\": \"消积化滞，行气止痛。用于气郁食滞所致的胸胁胀满，胃脘疼痛、嗳气呕恶，食少纳呆。\"}, {\"med_name\": \"开胸顺气丸\", \"indication\": \"消积化滞，行气止痛。用于气郁食滞所致的胸胁胀满，胃脘疼痛，嗳气呕恶，食少纳呆。\"}, {\"med_name\": \"开胸顺气丸\", \"indication\": \"消积化滞，行气止痛。用于饮食内停，气郁不舒导致的胸胁胀满，胃脘疼痛。\"}, {\"med_name\": \"开胸顺气丸\", \"indication\": \"消积化滞，行气止痛。用于气郁食滞所致的胸胁胀满、胃脘疼痛、嗳气呕恶、食少纳呆。\"}]}}" 
      // Truncated the original massive list for mock purposes to keep file size reasonable, but enough to show UI
    },
    {
      role: "tool_call",
      content: "{\"name\": \"query_database_by_sql\", \"arguments\": {\"sql\": \"SELECT DISTINCT med_name, component, indication, cate_name FROM drugs_info WHERE med_name LIKE '%开胸顺气丸%' LIMIT 5\"}}"
    },
    {
      role: "tool_response",
      content: "{\"result\": {\"status\": \"success\", \"records\": [{\"med_name\": \"开胸顺气丸\", \"component\": \"<p>开胸顺气成方</p>\\n\\n槟榔、牵牛子（炒）、陈皮、木香、厚朴（姜制）、三棱（醋制）、莪术（醋制）、猪牙皂。\", \"indication\": \"消积化滞，行气止痛。用于气郁食滞所致的胸胁胀满，胃脘疼痛、嗳气呕恶，食少纳呆。\", \"cate_name\": \"理气和中,通络止痛\"}, {\"med_name\": \"开胸顺气丸\", \"component\": \"槟榔、炒牵牛子、陈皮、木香、姜厚朴、醋三棱、醋莪术、猪牙皂。\", \"indication\": \"消积化滞，行气止痛。用于气郁食滞所致的胸胁胀满，胃脘疼痛，嗳气呕恶，食少纳呆。\", \"cate_name\": \"理气和中,通络止痛\"}], \"count\": 5}}"
    },
    {
      role: "assistant",
      content: "根据查询结果，**开胸顺气丸**主要用于治疗以下病症：\n\n## 主要功效：\n**消积化滞，行气止痛**\n\n## 适应症：\n开胸顺气丸主要用于治疗**气郁食滞**所致的以下症状：\n\n1. **胸胁胀满** - 胸部、两胁部感觉胀满不适\n2. **胃脘疼痛** - 胃部区域疼痛\n3. **嗳气呕恶** - 打嗝、恶心呕吐\n4. **食少纳呆** - 食欲不振，不想吃饭\n\n## 主治病机：\n- 饮食内停，气郁不舒\n- 停食停水，胸膈痞满\n- 脘腹胀痛，饮食少进\n\n## 主要成分：\n包含槟榔、牵牛子（炒）、陈皮、木香、厚朴（姜制）、三棱（醋制）、莪术（醋制）、猪牙皂等药材，具有理气宽胸、消积导滞的作用。\n\n## 简单来说：\n开胸顺气丸主要适用于因饮食积滞、气机郁结引起的消化不良症状，如胃胀、胃痛、打嗝恶心、食欲不振等消化系统问题。"
    }
  ],
  rejected_messages: [
    {
      role: "system",
      content: "..."
    },
    {
      role: "user",
      content: "药品开胸顺气丸的可以用来治什么？"
    },
    {
      role: "tool_call",
      content: "{\"name\": \"query_database_by_sql\", \"arguments\": {\"sql\": \"SELECT indication FROM drugs_info WHERE med_name = '开胸顺气丸'\"}}"
    },
    {
      role: "tool_response",
      content: "{\"result\": {\"status\": \"success\", \"records\": [{\"indication\": \"消积化滞，行气止痛。用于气郁食滞所致的胸胁胀满，胃脘疼痛、嗳气呕恶，食少纳呆。\"}]}}"
    },
    {
      role: "assistant",
      content: "药品开胸顺气丸主要用于以下症状：\n\n**功效**：消积化滞，行气止痛。\n\n**适用病症**：\n- 气郁食滞所致的胸胁胀满、胃脘疼痛；\n- 嗳气呕恶、食少纳呆；\n- 饮食内停、气郁不舒导致的胸胁胀满、胃脘疼痛；\n- 胸膈痞满、脘腹胀痛、饮食减少等。\n\n简而言之，适用于因气滞和食积引起的消化不良、胃部不适及胸闷等症状。"
    }
  ],
  metadata: {
    qid: "0e630842-e330-4aca-aab7-2b9b6c66ecc0",
    original_qid: "ced061ca-9420-43cf-970f-b7a94b78a976",
    task_type: "drug_field",
    question: "药品开胸顺气丸的可以用来治什么？",
    ground_truth: "药品开胸顺气丸主要用于治疗**气郁食滞**所引起的一系列消化不良症状。具体包括：\n\n1. **胸胁胀满**：胸部或肋骨两侧感觉胀闷不适。\n2. **胃脘疼痛**：胃部区域出现疼痛。\n3. **嗳气呕恶**：打嗝、反胃、恶心感。\n4. **食少纳呆**：食欲下降，不想吃饭。\n\n总结来说，它适用于因情绪不畅、饮食积滞导致的上述消化道不适。",
    chosen_model: "deepseek-v3.2",
    models: {
      "deepseek-v3.2": "deepseek-v3.2",
      "qwen-turbo-latest": "qwen-turbo-latest"
    },
    created_at: "2026-01-30"
  }
};