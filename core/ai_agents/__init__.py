#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI Agents 主模块

基于PocketFlow的AI代理系统，使用重构后的标准化节点、流程和代理管理。
"""

import logging

logger = logging.getLogger(__name__)

# 🔄 标准化接口
from .interfaces import BaseAgent, BaseFlow, BaseNode, BaseAnalysisNode

# 🔄 重构后的节点
from .nodes.analysis.news_classifier_node import NewsClassifierNode
from .nodes.analysis.stock_analyzer_node import StockAnalyzerNode
from .nodes.decision.investment_advisor_node import InvestmentAdvisorNode

# 🔄 流程和结果类
from .flow_definitions.news_analysis_flow import (
    NewsAnalysisFlow,
    EnhancedNewsAnalysisResult,
    analyze_single_news
)

# 🔄 统一的导出列表
__all__ = [
    # 标准化接口
    "BaseAgent", 
    "BaseFlow", 
    "BaseNode", 
    "BaseAnalysisNode",
    
    # 重构后的节点
    "NewsClassifierNode", 
    "StockAnalyzerNode", 
    "InvestmentAdvisorNode",
    
    # 流程和结果类
    "NewsAnalysisFlow",
    "EnhancedNewsAnalysisResult",
    "analyze_single_news",
    
    # 便捷函数
    "create_news_analysis_flow",
    "quick_analyze_news"
]

# 🔄 版本信息
__version__ = "2.0.0-refactored"
__status__ = "🔄 重构版本"
__author__ = "InvestNote AI Team"
__description__ = "基于PocketFlow的多Agent新闻分析系统"

# 🔄 模块级别的便捷函数
def create_news_analysis_flow(llm_client, test_mode: bool = False):
    """
    创建新闻分析流程的便捷函数
    
    Args:
        llm_client: LLM客户端实例
        test_mode: 是否为测试模式，避免数据库连接
        
    Returns:
        NewsAnalysisFlow实例
    """
    try:
        return NewsAnalysisFlow(llm_client, test_mode=test_mode)
    except Exception as e:
        logger.error(f"创建新闻分析流程失败: {e}")
        raise

def quick_analyze_news(news_content: str, news_id: str = None, test_mode: bool = False):
    """
    快速分析新闻的便捷函数
    
    Args:
        news_content: 新闻内容
        news_id: 新闻ID（可选）
        test_mode: 是否为测试模式，避免数据库连接
        
    Returns:
        分析结果
    """
    try:
        return analyze_single_news(news_content, news_id, test_mode)
    except Exception as e:
        logger.error(f"快速新闻分析失败: {e}")
        raise

logger.info(f"✅ AI Agents模块已加载: {__version__} - {__status__}") 