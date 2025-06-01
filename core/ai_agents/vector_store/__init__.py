#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
向量存储模块
提供新闻文章的向量化存储和相似性分析功能
"""

from .chroma_store import (
    ChromaNewsStore,
    get_chroma_store
)

from .vector_similarity import (
    VectorSimilarityAnalyzer,
    get_similarity_analyzer
)

__all__ = [
    # ChromaDB存储
    'ChromaNewsStore',
    'get_chroma_store',
    
    # 相似性分析
    'VectorSimilarityAnalyzer',
    'get_similarity_analyzer'
]
