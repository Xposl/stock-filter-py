#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
InvestNote-py - 投资笔记和分析系统

基于FastAPI的投资数据分析平台，集成AI分析、新闻聚合和量化策略。
"""

__version__ = "1.0.0"
__author__ = "InvestNote Team"
__description__ = "投资笔记和分析系统"

import sys
import os

# 确保项目根目录在Python路径中
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root) 