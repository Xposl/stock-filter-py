#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Agents 节点模块

包含所有类型的处理节点：数据摄取、分析、决策、输出
"""

# 分析节点
from .analysis.news_classifier_node import NewsClassifierNode
from .analysis.stock_analyzer_node import StockAnalyzerNode
from .decision.investment_advisor_node import InvestmentAdvisorNode

__all__ = [
    "NewsClassifierNode",
    "StockAnalyzerNode", 
    "InvestmentAdvisorNode"
] 