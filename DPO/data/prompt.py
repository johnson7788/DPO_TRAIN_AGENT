#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date  : 2025/12/09 12:00
# @File  : prompt.py
# @Desc  :  搜索Agent
from datetime import datetime
today = datetime.today().strftime('%Y-%m-%d')
# today = "2025年12月25日"
# f"重要提醒：今天日期是: {today}" +
QA_prompt = f"""
按需使用sql进行query_database_by_sql执行查询，然后回答用户的问题。
表结构如下:
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
"""
