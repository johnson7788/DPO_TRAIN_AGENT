#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date  : 2025/12/27
# @File  : database_tools.py
# @Desc  : 数据库工具函数 - 支持药品和疾病查询

import sqlite3
import json
from typing import List, Dict, Any, Optional
import random

DATABASE_PATH = "medical_data.db"

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ==================== 任务族1: 药品查询工具 ====================

def search_drug(keyword: str) -> List[Dict[str, Any]]:
    """
    按药名/拼音/条码搜索药品

    Args:
        keyword: 搜索关键词

    Returns:
        药品列表,每个包含 id, med_name, indication 等关键字段
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT id, med_name, med_name_initial, med_barcode, indication,
           dosage, contraindications, adverse_reactions, component,
           company_name, description, mechanism_action
    FROM drugs_info
    WHERE med_name LIKE ?
       OR med_name_initial LIKE ?
       OR med_barcode LIKE ?
    LIMIT 10
    """
    cursor.execute(query, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results

def get_drug(drug_id: int) -> Optional[Dict[str, Any]]:
    """
    获取药品详细信息

    Args:
        drug_id: 药品ID

    Returns:
        药品完整信息字典
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT * FROM drugs_info WHERE id = ?
    """
    cursor.execute(query, (drug_id,))
    result = cursor.fetchone()
    conn.close()

    return dict(result) if result else None

# ==================== 任务族2: 疾病查询工具 ====================

def search_disease(keyword: str) -> List[Dict[str, Any]]:
    """
    按疾病名搜索

    Args:
        keyword: 搜索关键词

    Returns:
        疾病列表,每个包含 id, disease_name, clinical_manif 等关键字段
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT id, disease_name, clinical_manif, treatment, diagnosis,
           examination, prevention, complication, overview
    FROM disease
    WHERE disease_name LIKE ?
    LIMIT 10
    """
    cursor.execute(query, (f"%{keyword}%",))
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results

def get_disease(disease_id: int) -> Optional[Dict[str, Any]]:
    """
    获取疾病详细信息

    Args:
        disease_id: 疾病ID

    Returns:
        疾病完整信息字典
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT * FROM disease WHERE id = ?
    """
    cursor.execute(query, (disease_id,))
    result = cursor.fetchone()
    conn.close()

    return dict(result) if result else None

# ==================== 辅助函数 ====================

def check_database_exists() -> bool:
    """检查数据库文件是否存在"""
    import os
    return os.path.exists(DATABASE_PATH)

def get_table_info(table_name: str) -> List[str]:
    """获取表的字段信息"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    conn.close()

    return columns

def sample_random_drug() -> Optional[Dict[str, Any]]:
    """随机采样一条药品记录"""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM drugs_info ORDER BY RANDOM() LIMIT 1"
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()

    return dict(result) if result else None

def sample_random_disease() -> Optional[Dict[str, Any]]:
    """随机采样一条疾病记录"""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM disease ORDER BY RANDOM() LIMIT 1"
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()

    return dict(result) if result else None


if __name__ == "__main__":
    # 测试数据库连接和基本功能
    print("=" * 80)
    print("测试数据库工具函数")
    print("=" * 80)

    # 检查数据库是否存在
    if not check_database_exists():
        print(f"❌ 数据库文件不存在: {DATABASE_PATH}")
        exit(1)

    print(f"✅ 数据库文件存在: {DATABASE_PATH}")

    # 测试搜索药品
    print("\n--- 测试 search_drug ---")
    drugs = search_drug("阿司匹林")
    print(f"找到 {len(drugs)} 条药品记录")
    if drugs:
        print(f"第一条: {drugs[0]['med_name']}")

    # 测试搜索疾病
    print("\n--- 测试 search_disease ---")
    diseases = search_disease("高血压")
    print(f"找到 {len(diseases)} 条疾病记录")
    if diseases:
        print(f"第一条: {diseases[0]['disease_name']}")

    # 测试随机采样
    print("\n--- 测试随机采样 ---")
    random_drug = sample_random_drug()
    if random_drug:
        print(f"随机药品: {random_drug['med_name']}")

    random_disease = sample_random_disease()
    if random_disease:
        print(f"随机疾病: {random_disease['disease_name']}")

    print("\n✅ 所有测试通过!")