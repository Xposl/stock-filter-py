#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LLM客户端模块
提供统一的LLM访问接口，支持千问和硅基流动API
"""

from .qwen_client import (
    QwenLLMClient,
    QwenResponse,
    TokenUsage,
    TokenCalculator,
    get_qwen_client,
    quick_analyze
)

from .silicon_flow_client import (
    SiliconFlowClient,
    SiliconFlowResponse,
    get_silicon_flow_client
)

__all__ = [
    # 千问客户端
    'QwenLLMClient',
    'QwenResponse', 
    'TokenUsage',
    'TokenCalculator',
    'get_qwen_client',
    'quick_analyze',
    
    # 硅基流动客户端
    'SiliconFlowClient',
    'SiliconFlowResponse',
    'get_silicon_flow_client'
]
