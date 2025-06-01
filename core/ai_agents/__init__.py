#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Agents 模块

基于PocketFlow框架的AI分析代理系统，专为InvestNote-py新闻分析设计。
GitHub: https://github.com/The-Pocket/PocketFlow

主要功能：
- 新闻智能分析和情感识别
- 投资机会自动检测和评估
- 股票关联度计算和投资建议
- 基于向量数据库的语义相似性分析

核心架构：
- PocketFlow: 100行LLM工作流框架
- 千问LLM: 阿里云大语言模型服务
- ChromaDB: 嵌入式向量数据库
- 四层处理流水线: 预筛选→AI分析→情感评估→投资建议
"""

# 导入已存在的模块
from . import llm_clients
from . import vector_store
from . import flow_definitions
from . import analyzers
from . import utils

__version__ = "1.0.0"
__author__ = "InvestNote-py Team"
__framework__ = "PocketFlow v0.0.2"

__all__ = [
    "llm_clients",
    "vector_store", 
    "flow_definitions",
    "analyzers",
    "utils"
] 