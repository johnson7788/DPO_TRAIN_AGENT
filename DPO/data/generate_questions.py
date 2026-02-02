#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
问题数据生成器
用于生成带 Ground Truth 的 QA 数据集

生成三类任务：
A. 单表字段抽取 (drug_field / disease_field)
B. 同表对比 (compare_drugs / compare_diseases)
C. 关键词检索 (drug_search_by_kw)
"""

import asyncio
import json
import random
import re
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from itertools import combinations

from llm_invoke import generate_answer


# -----------------------------------------------------------------------------
# 配置
# -----------------------------------------------------------------------------

DATABASE_PATH = "medical_data.db"

# 药品字段配置
DRUG_FIELDS = {
    "indication": {
        "question_templates": [
            "适应症是什么？",
            "适用于哪些疾病？",
            "主要用于治疗什么病？",
            "可以用来治什么？",
            "适应症包括哪些？",
        ],
        "aliases": ["适应症", "用于", "治疗", "主治"]
    },
    "contraindications": {
        "question_templates": [
            "禁忌症有哪些？",
            "哪些情况下不能用？",
            "禁忌人群有哪些？",
            "什么情况需要慎用？",
        ],
        "aliases": ["禁忌", "不能用", "慎用"]
    },
    "adverse_reactions": {
        "question_templates": [
            "有哪些不良反应？",
            "服用后会有什么副作用？",
            "可能出现的不良反应有哪些？",
        ],
        "aliases": ["不良反应", "副作用"]
    },
    "dosage": {
        "question_templates": [
            "用法用量是怎样的？",
            "应该如何服用？",
            "剂量如何？",
        ],
        "aliases": ["用法", "用量", "剂量", "服用"]
    },
    "precautions": {
        "question_templates": [
            "有哪些注意事项？",
            "服用前需要注意什么？",
            "有什么需要特别注意的？",
        ],
        "aliases": ["注意", "注意事项", "需要"]
    },
    "adverse_reactions": {
        "question_templates": [
            "不良反应有哪些？",
            "服用后可能有哪些副作用？",
            "有什么不良反应需要注意？",
        ],
        "aliases": ["不良反应", "副作用"]
    }
}

# 疾病字段配置
DISEASE_FIELDS = {
    "clinical_manif": {
        "question_templates": [
            "临床表现有哪些？",
            "症状是什么？",
            "有哪些临床特征？",
        ],
        "aliases": ["临床", "症状", "表现"]
    },
    "treatment": {
        "question_templates": [
            "如何治疗？",
            "治疗方法有哪些？",
            "应该如何处理？",
        ],
        "aliases": ["治疗", "治疗方案", "疗法"]
    },
    "diagnosis": {
        "question_templates": [
            "如何诊断？",
            "诊断方法有哪些？",
            "需要做什么检查？",
        ],
        "aliases": ["诊断", "检查"]
    },
    "prevention": {
        "question_templates": [
            "如何预防？",
            "预防措施有哪些？",
            "应该如何预防？",
        ],
        "aliases": ["预防", "预防措施"]
    }
}

# 药品对比字段
DRUG_COMPARE_FIELDS = ["contraindications", "adverse_reactions", "precautions", "indication"]

# 疾病对比字段
DISEASE_COMPARE_FIELDS = ["clinical_manif", "treatment", "diagnosis"]


# -----------------------------------------------------------------------------
# 工具函数
# -----------------------------------------------------------------------------

async def get_db_connection():
    """获取数据库连接（同步版本）"""
    import sqlite3
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


async def execute_query(sql: str) -> List[Dict[str, Any]]:
    """执行SQL查询"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute(sql)
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results
    except sqlite3.Error as e:
        print(f"SQL执行错误: {e}")
        return []
    finally:
        conn.close()


async def get_all_drugs(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """获取所有药品"""
    sql = "SELECT * FROM drugs_info WHERE med_name IS NOT NULL AND med_name != ''"
    if limit:
        sql += f" LIMIT {limit}"
    return await execute_query(sql)


async def get_all_diseases(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """获取所有疾病"""
    sql = "SELECT * FROM disease WHERE disease_name IS NOT NULL AND disease_name != ''"
    if limit:
        sql += f" LIMIT {limit}"
    return await execute_query(sql)


def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """从文本中提取关键词"""
    if not text:
        return []
    
    # 简单分词，去除停用词
    stopwords = {"的", "是", "在", "了", "和", "与", "或", "等", "有", "为", "于", "从", "到", "被", "可", "能", "会", "要", "请", "您", "我", "他", "她", "它", "这", "那", "哪些", "什么", "如何", "怎么", "怎样", "是否", "能不能", "能不能够"}
    
    words = [w.strip() for w in re.split(r'[,\s，。；；：""\'\'"\'\'"\'\'"\'\'"\'\'"\'\'"\'\'"\'\'"\'\'"\'\'"\'\'"\'\'"\'\'"\′″∶～·、]', text) if w.strip() and len(w.strip()) > 1]
    
    # 过滤停用词
    keywords = [w for w in words if w not in stopwords]
    
    # 返回出现频率较高的词
    return list(set(keywords))[:max_keywords]


def truncate_text(text: str, max_length: int = 200) -> str:
    """截断文本，保留完整句子"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    # 尝试在句号、逗号处截断
    for sep in ["。", "；", "，", "！", "？", "\n"]:
        idx = text.rfind(sep, 0, max_length)
        if idx > max_length * 0.6:
            return text[:idx + 1]
    
    return text[:max_length] + "..."


def generate_qid() -> str:
    """生成唯一问题ID"""
    return str(uuid.uuid4())


def current_date() -> str:
    """返回当前日期"""
    return datetime.now().strftime("%Y-%m-%d")


# -----------------------------------------------------------------------------
# 任务 A: 单表字段抽取
# -----------------------------------------------------------------------------

async def generate_drug_field_task(drug: Dict[str, Any], field: str) -> Optional[Dict[str, Any]]:
    """生成药品字段抽取任务"""
    field_value = drug.get(field)
    if not field_value or str(field_value).strip() == "":
        return None

    config = DRUG_FIELDS.get(field)
    if not config:
        return None

    # 随机选择问题模板
    question_template = random.choice(config["question_templates"])
    question = f"药品{drug['med_name']}的{question_template}"

    # 生成SQL
    sql = f"SELECT {field} FROM drugs_info WHERE id = {drug['id']}"

    # 生成 evidence
    evidence = [{
        "source_table": "drugs_info",
        "row_id": drug["id"],
        "field": field,
        "quote": str(field_value)
    }]

    return {
        "qid": generate_qid(),
        "task_type": "drug_field",
        "question": question,
        "sql": [sql],
        "evidence": evidence,
        "meta": {
            "entity": {"drug_name": drug["med_name"], "drug_id": drug["id"]},
            "created_at": current_date()
        }
    }


async def generate_disease_field_task(disease: Dict[str, Any], field: str) -> Optional[Dict[str, Any]]:
    """生成疾病字段抽取任务"""
    field_value = disease.get(field)
    if not field_value or str(field_value).strip() == "":
        return None

    config = DISEASE_FIELDS.get(field)
    if not config:
        return None

    # 随机选择问题模板
    question_template = random.choice(config["question_templates"])
    question = f"{disease['disease_name']}的{question_template}"

    # 生成SQL
    sql = f"SELECT {field} FROM disease WHERE id = {disease['id']}"

    # 生成 evidence
    evidence = [{
        "source_table": "disease",
        "row_id": disease["id"],
        "field": field,
        "quote": str(field_value)
    }]

    return {
        "qid": generate_qid(),
        "task_type": "disease_field",
        "question": question,
        "sql": [sql],
        "evidence": evidence,
        "meta": {
            "entity": {"disease_name": disease["disease_name"], "disease_id": disease["id"]},
            "created_at": current_date()
        }
    }


# -----------------------------------------------------------------------------
# 任务 B: 同表对比
# -----------------------------------------------------------------------------

async def generate_drug_compare_task(drug1: Dict[str, Any], drug2: Dict[str, Any], field: str) -> Optional[Dict[str, Any]]:
    """生成药品对比任务"""
    value1 = drug1.get(field)
    value2 = drug2.get(field)

    if not value1 or not value2:
        return None

    config = DRUG_FIELDS.get(field)
    field_cn = config["question_templates"][0].replace("有哪些", "").replace("是什么", "") if config else field

    question = f"对比{drug1['med_name']}和{drug2['med_name']}的{field_cn}有什么不同？"

    # 生成SQL
    sql = f"SELECT id, med_name, {field} FROM drugs_info WHERE id IN ({drug1['id']}, {drug2['id']})"

    # 生成 evidence
    evidence = [
        {
            "source_table": "drugs_info",
            "row_id": drug1["id"],
            "field": field,
            "quote": str(value1)
        },
        {
            "source_table": "drugs_info",
            "row_id": drug2["id"],
            "field": field,
            "quote": str(value2)
        }
    ]

    return {
        "qid": generate_qid(),
        "task_type": "compare_drugs",
        "question": question,
        "sql": [sql],
        "evidence": evidence,
        "meta": {
            "entity": {
                "drug_name_a": drug1["med_name"],
                "drug_name_b": drug2["med_name"],
                "drug_id_a": drug1["id"],
                "drug_id_b": drug2["id"]
            },
            "created_at": current_date()
        }
    }


async def generate_disease_compare_task(disease1: Dict[str, Any], disease2: Dict[str, Any], field: str) -> Optional[Dict[str, Any]]:
    """生成疾病对比任务"""
    value1 = disease1.get(field)
    value2 = disease2.get(field)

    if not value1 or not value2:
        return None

    config = DISEASE_FIELDS.get(field)
    field_cn = config["question_templates"][0].replace("有哪些", "").replace("是什么", "") if config else field

    question = f"对比{disease1['disease_name']}和{disease2['disease_name']}的{field_cn}有什么不同？"

    # 生成SQL
    sql = f"SELECT id, disease_name, {field} FROM disease WHERE id IN ({disease1['id']}, {disease2['id']})"

    # 生成 evidence
    evidence = [
        {
            "source_table": "disease",
            "row_id": disease1["id"],
            "field": field,
            "quote": str(value1)
        },
        {
            "source_table": "disease",
            "row_id": disease2["id"],
            "field": field,
            "quote": str(value2)
        }
    ]

    return {
        "qid": generate_qid(),
        "task_type": "compare_diseases",
        "question": question,
        "sql": [sql],
        "evidence": evidence,
        "meta": {
            "entity": {
                "disease_name_a": disease1["disease_name"],
                "disease_name_b": disease2["disease_name"],
                "disease_id_a": disease1["id"],
                "disease_id_b": disease2["id"]
            },
            "created_at": current_date()
        }
    }


# -----------------------------------------------------------------------------
# 任务 C: 关键词检索
# -----------------------------------------------------------------------------

async def generate_keyword_search_task(keyword: str, top_k: int = 3) -> Optional[Dict[str, Any]]:
    """生成关键词检索任务"""
    # 搜索包含关键词的药品
    sql = f"""
    SELECT id, med_name, indication
    FROM drugs_info
    WHERE indication LIKE '%{keyword}%'
    LIMIT {top_k}
    """

    results = await execute_query(sql)

    if not results:
        return None

    # 构建命中信息
    hits = []
    for row in results:
        indication = row.get("indication", "")
        # 找到关键词位置
        idx = indication.lower().find(keyword.lower())
        if idx >= 0:
            start = max(0, idx - 30)
            end = min(len(indication), idx + len(keyword) + 30)
            quote = indication[start:end]
        else:
            quote = indication[:100]

        hits.append({
            "drug_id": row["id"],
            "drug_name": row["med_name"],
            "match_position": idx if idx >= 0 else None,
            "quote": quote
        })

    question = f"适应症包含{keyword}的药品有哪些？列出前{top_k}个。"

    # 生成 evidence
    evidence = [
        {
            "source_table": "drugs_info",
            "row_id": hit["drug_id"],
            "field": "indication",
            "quote": hit["quote"]
        }
        for hit in hits
    ]

    return {
        "qid": generate_qid(),
        "task_type": "drug_search_by_kw",
        "question": question,
        "sql": [sql],
        "evidence": evidence,
        "meta": {
            "entity": {"keyword": keyword},
            "created_at": current_date()
        }
    }


# -----------------------------------------------------------------------------
# 主生成函数
# -----------------------------------------------------------------------------

async def generate_and_save_dataset(
    total_samples: int = 1000,
    drug_ratio: float = 0.3,
    disease_ratio: float = 0.3,
    compare_ratio: float = 0.3,
    keyword_ratio: float = 0.1,
    sample_drugs: int = 500,
    sample_diseases: int = 300,
    output_file: str = "qa_dataset.jsonl"
) -> int:
    """生成并实时保存数据集（JSONL格式）

    Args:
        total_samples: 总样本数（默认1000）
        drug_ratio: 药品字段抽取任务占比
        disease_ratio: 疾病字段抽取任务占比
        compare_ratio: 对比任务占比（药品+疾病）
        keyword_ratio: 关键词检索任务占比
        sample_drugs: 从数据库采样的药品数量
        sample_diseases: 从数据库采样的疾病数量
        output_file: 输出文件路径（JSONL格式）

    Returns:
        成功生成并保存的任务数量
    """

    # 计算各类任务数量
    num_drug_field = int(total_samples * drug_ratio)
    num_disease_field = int(total_samples * disease_ratio)
    num_compare = int(total_samples * compare_ratio)
    num_keyword = int(total_samples * keyword_ratio)

    print(f"目标生成 {total_samples} 条数据:")
    print(f"  - 药品字段抽取: {num_drug_field}")
    print(f"  - 疾病字段抽取: {num_disease_field}")
    print(f"  - 对比任务: {num_compare}")
    print(f"  - 关键词检索: {num_keyword}")

    # 获取实体（随机采样）
    print(f"\n正在从数据库随机采样药品（{sample_drugs}个）...")
    drugs = await get_all_drugs()
    if len(drugs) > sample_drugs:
        drugs = random.sample(drugs, min(sample_drugs, len(drugs)))
    print(f"获取到 {len(drugs)} 个药品")

    print(f"正在从数据库随机采样疾病（{sample_diseases}个）...")
    diseases = await get_all_diseases()
    if len(diseases) > sample_diseases:
        diseases = random.sample(diseases, min(sample_diseases, len(diseases)))
    print(f"获取到 {len(diseases)} 个疾病")

    # 打乱顺序以确保随机性
    random.shuffle(drugs)
    random.shuffle(diseases)

    # 打开输出文件（JSONL格式）
    with open(output_file, "w", encoding="utf-8") as f:
        saved_count = 0

        # 任务 A: 药品字段抽取
        print("\n生成药品字段抽取任务...")
        drug_count = 0
        drug_fields = list(DRUG_FIELDS.keys())
        random.shuffle(drug_fields)

        for drug in drugs:
            for field in drug_fields:
                if drug_count >= num_drug_field:
                    break
                task = await generate_drug_field_task(drug, field)
                if task:
                    # 生成 ground_truth
                    question = task.get("question", "")
                    evidence = task.get("evidence", [])
                    success, answer = await generate_answer(question, evidence)
                    task["ground_truth"] = answer if success else ""

                    # 实时保存（JSONL格式，每行一条）
                    f.write(json.dumps(task, ensure_ascii=False) + "\n")
                    saved_count += 1
                    drug_count += 1
            if drug_count >= num_drug_field:
                break
        print(f"完成: {drug_count} 条")

        # 任务 A: 疾病字段抽取
        print("生成疾病字段抽取任务...")
        disease_count = 0
        disease_fields = list(DISEASE_FIELDS.keys())
        random.shuffle(disease_fields)

        for disease in diseases:
            for field in disease_fields:
                if disease_count >= num_disease_field:
                    break
                task = await generate_disease_field_task(disease, field)
                if task:
                    # 生成 ground_truth
                    question = task.get("question", "")
                    evidence = task.get("evidence", [])
                    success, answer = await generate_answer(question, evidence)
                    task["ground_truth"] = answer if success else ""

                    # 实时保存
                    f.write(json.dumps(task, ensure_ascii=False) + "\n")
                    saved_count += 1
                    disease_count += 1
            if disease_count >= num_disease_field:
                break
        print(f"完成: {disease_count} 条")

        # 任务 B: 药品对比
        print("生成药品对比任务...")
        drug_compare_num = num_compare // 2
        drug_compare_count = 0
        drug_pairs = list(combinations(drugs, 2))
        random.shuffle(drug_pairs)

        for drug1, drug2 in drug_pairs:
            if drug_compare_count >= drug_compare_num:
                break
            field = random.choice(DRUG_COMPARE_FIELDS)
            task = await generate_drug_compare_task(drug1, drug2, field)
            if task:
                # 生成 ground_truth
                question = task.get("question", "")
                evidence = task.get("evidence", [])
                success, answer = await generate_answer(question, evidence)
                task["ground_truth"] = answer if success else ""

                # 实时保存
                f.write(json.dumps(task, ensure_ascii=False) + "\n")
                saved_count += 1
                drug_compare_count += 1
        print(f"完成: {drug_compare_count} 条")

        # 任务 B: 疾病对比
        print("生成疾病对比任务...")
        disease_compare_num = num_compare - drug_compare_num
        disease_compare_count = 0
        disease_pairs = list(combinations(diseases, 2))
        random.shuffle(disease_pairs)

        for disease1, disease2 in disease_pairs:
            if disease_compare_count >= disease_compare_num:
                break
            field = random.choice(DISEASE_COMPARE_FIELDS)
            task = await generate_disease_compare_task(disease1, disease2, field)
            if task:
                # 生成 ground_truth
                question = task.get("question", "")
                evidence = task.get("evidence", [])
                success, answer = await generate_answer(question, evidence)
                task["ground_truth"] = answer if success else ""

                # 实时保存
                f.write(json.dumps(task, ensure_ascii=False) + "\n")
                saved_count += 1
                disease_compare_count += 1
        print(f"完成: {disease_compare_count} 条")

        # 任务 C: 关键词检索
        print("生成关键词检索任务...")
        all_keywords = set()
        for drug in drugs:
            kw = extract_keywords(drug.get("indication", ""))
            all_keywords.update(kw)

        keyword_list = random.sample(list(all_keywords), min(num_keyword, len(all_keywords)))

        keyword_count = 0
        for keyword in keyword_list:
            task = await generate_keyword_search_task(keyword)
            if task:
                # 生成 ground_truth
                question = task.get("question", "")
                evidence = task.get("evidence", [])
                success, answer = await generate_answer(question, evidence)
                task["ground_truth"] = answer if success else ""

                # 实时保存
                f.write(json.dumps(task, ensure_ascii=False) + "\n")
                saved_count += 1
                keyword_count += 1
        print(f"完成: {keyword_count} 条")

    print(f"\n数据集已保存到: {output_file}，共 {saved_count} 条（JSONL格式）")
    return saved_count


# -----------------------------------------------------------------------------
# 主入口
# -----------------------------------------------------------------------------

async def main():
    """主函数"""
    print("=" * 50)
    print("开始生成 QA 数据集...")
    print("格式: JSONL（每行一条，实时保存）")
    print("目标: 1000条，随机均衡采样")
    print("=" * 50)

    # 生成并实时保存数据集
    saved_count = await generate_and_save_dataset(
        total_samples=1000,      # 总样本数
        drug_ratio=0.3,          # 30% 药品字段
        disease_ratio=0.3,       # 30% 疾病字段
        compare_ratio=0.3,       # 30% 对比任务
        keyword_ratio=0.1,       # 10% 关键词检索
        sample_drugs=500,        # 采样500个药品（数据库有10万）
        sample_diseases=300,     # 采样300个疾病（数据库有7000）
        output_file="qa_dataset.jsonl"
    )
    print(f"\n完成！共生成 {saved_count} 条数据")


if __name__ == "__main__":
    asyncio.run(main())
