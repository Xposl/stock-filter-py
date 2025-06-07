#!/usr/bin/env python3

"""
LLM客户端模块
提供统一的LLM访问接口，支持千问和硅基流动API
基于OpenAI设计模式实现
"""

from .qwen_client import (  # 客户端类; 响应和消息类; 全局客户端获取函数; 便捷函数
    AsyncQwenClient,
    QwenClient,
    QwenLLMClient,  # 向后兼容别名
    QwenMessage,
    QwenResponse,
    QwenStreamResponse,
    async_chat,
    async_stream_chat,
    chat,
    get_async_qwen_client,
    get_qwen_client,
    stream_chat,
)

# 硅基流动客户端暂未实现，先注释掉
# from .silicon_flow_client import (
#     SiliconFlowClient,
#     SiliconFlowResponse,
#     get_silicon_flow_client
# )

__all__ = [
    # 千问客户端类
    "QwenClient",
    "AsyncQwenClient",
    "QwenLLMClient",  # 向后兼容
    # 响应和消息类
    "QwenResponse",
    "QwenStreamResponse",
    "QwenMessage",
    # 全局客户端函数
    "get_qwen_client",
    "get_async_qwen_client",
    # 便捷函数
    "chat",
    "async_chat",
    "stream_chat",
    "async_stream_chat",
    # 硅基流动客户端（暂未实现）
    # 'SiliconFlowClient',
    # 'SiliconFlowResponse',
    # 'get_silicon_flow_client'
]
