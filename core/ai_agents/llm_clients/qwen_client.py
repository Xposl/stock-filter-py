#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
千问LLM客户端

基于阿里云千问模型的LLM客户端，提供OpenAI兼容的接口格式。
支持异步调用、Token计算、成本监控等功能。
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass
import aiohttp
import tiktoken
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class QwenResponse:
    """千问API响应数据结构"""
    content: str
    usage: Dict[str, int]
    model: str
    finish_reason: str
    created_at: datetime

@dataclass
class TokenUsage:
    """Token使用统计"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float

class QwenLLMClient:
    """
    千问LLM客户端
    
    提供OpenAI兼容的异步接口，支持：
    - 异步调用和批量处理
    - Token计算和成本监控  
    - 错误处理和重试机制
    - 请求日志和性能监控
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "qwen-turbo",
        max_retries: int = 3,
        timeout: int = 30
    ):
        """
        初始化千问客户端
        
        Args:
            api_key: 千问API密钥
            base_url: API基础URL
            model: 使用的模型名称
            max_retries: 最大重试次数
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key or os.getenv('QWEN_API_KEY')
        self.base_url = base_url or os.getenv('QWEN_BASE_URL', 'https://dashscope.aliyuncs.com/api/v1')
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        
        if not self.api_key:
            raise ValueError("千问API密钥未配置，请设置QWEN_API_KEY环境变量")
        
        # Token计算器（使用gpt-3.5-turbo的编码器作为估算）
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
        except Exception:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # 成本配置（每1000个token的价格，单位：元）
        self.token_prices = {
            "qwen-turbo": {"input": 0.002, "output": 0.006},
            "qwen-plus": {"input": 0.004, "output": 0.012},
            "qwen-max": {"input": 0.02, "output": 0.06}
        }
        
        # 会话管理
        self.session: Optional[aiohttp.ClientSession] = None
        self._own_session = False
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json'
                }
            )
            self._own_session = True
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self._own_session and self.session:
            await self.session.close()
            self.session = None
    
    def count_tokens(self, text: str) -> int:
        """
        计算文本的Token数量
        
        Args:
            text: 要计算的文本
            
        Returns:
            Token数量
        """
        try:
            return len(self.tokenizer.encode(text))
        except Exception as e:
            logger.warning(f"Token计算失败，使用估算值: {e}")
            # 简单估算：中文约1.5字符/token，英文约4字符/token
            chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
            other_chars = len(text) - chinese_chars
            return int(chinese_chars / 1.5 + other_chars / 4)
    
    def calculate_cost(self, usage: TokenUsage) -> float:
        """
        计算调用成本
        
        Args:
            usage: Token使用统计
            
        Returns:
            成本（元）
        """
        prices = self.token_prices.get(self.model, self.token_prices["qwen-turbo"])
        
        input_cost = (usage.prompt_tokens / 1000) * prices["input"]
        output_cost = (usage.completion_tokens / 1000) * prices["output"]
        
        return input_cost + output_cost
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> QwenResponse:
        """
        OpenAI兼容的聊天完成接口
        
        Args:
            messages: 对话消息列表
            temperature: 随机性控制
            max_tokens: 最大生成Token数
            stream: 是否流式输出
            
        Returns:
            千问响应对象
        """
        if not self.session:
            raise RuntimeError("客户端未初始化，请使用async with语句")
        
        # 构建请求数据
        request_data = {
            "model": self.model,
            "input": {
                "messages": messages
            },
            "parameters": {
                "temperature": temperature,
                "result_format": "message"
            }
        }
        
        if max_tokens:
            request_data["parameters"]["max_tokens"] = max_tokens
        
        # 计算输入Token数
        prompt_text = json.dumps(messages, ensure_ascii=False)
        prompt_tokens = self.count_tokens(prompt_text)
        
        logger.info(f"发送千问请求，模型: {self.model}, 输入tokens: {prompt_tokens}")
        
        # 发送请求并重试
        for attempt in range(self.max_retries):
            try:
                async with self.session.post(
                    f"{self.base_url}/services/aigc/text-generation/generation",
                    json=request_data
                ) as response:
                    response_data = await response.json()
                    
                    if response.status == 200 and response_data.get("output"):
                        # 解析响应
                        output = response_data["output"]
                        content = output["text"]
                        finish_reason = output.get("finish_reason", "stop")
                        
                        # 计算输出Token数和成本
                        completion_tokens = self.count_tokens(content)
                        usage = TokenUsage(
                            prompt_tokens=prompt_tokens,
                            completion_tokens=completion_tokens,
                            total_tokens=prompt_tokens + completion_tokens,
                            estimated_cost=0.0
                        )
                        usage.estimated_cost = self.calculate_cost(usage)
                        
                        logger.info(f"千问请求成功，输出tokens: {completion_tokens}, 成本: ¥{usage.estimated_cost:.4f}")
                        
                        return QwenResponse(
                            content=content,
                            usage=usage.__dict__,
                            model=self.model,
                            finish_reason=finish_reason,
                            created_at=datetime.now()
                        )
                    else:
                        # API错误响应
                        error_msg = response_data.get("message", "未知错误")
                        raise Exception(f"千问API错误: {error_msg}")
                        
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"千问请求失败，已重试{self.max_retries}次: {e}")
                    raise
                else:
                    logger.warning(f"千问请求失败，第{attempt + 1}次重试: {e}")
                    await asyncio.sleep(2 ** attempt)  # 指数退避
    
    async def analyze_news_batch(
        self,
        articles: List[Dict[str, Any]],
        analysis_prompt: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        批量分析新闻文章
        
        Args:
            articles: 新闻文章列表
            analysis_prompt: 分析提示词模板
            
        Returns:
            分析结果列表
        """
        if not analysis_prompt:
            analysis_prompt = """
请分析以下新闻文章的投资价值和市场影响：

{articles}

请为每篇文章提供：
1. 情感倾向（积极/中性/消极）
2. 市场影响度（高/中/低）
3. 相关股票代码
4. 投资建议（买入/持有/卖出）
5. 风险等级（高/中/低）

请以JSON格式返回结果。
"""
        
        # 将文章列表格式化为文本
        articles_text = ""
        for i, article in enumerate(articles, 1):
            title = article.get("title", "无标题")
            content = article.get("content", "")[:500]  # 限制内容长度
            articles_text += f"{i}. 标题: {title}\n内容: {content}\n\n"
        
        messages = [
            {"role": "user", "content": analysis_prompt.format(articles=articles_text)}
        ]
        
        response = await self.chat_completion(messages, temperature=0.3)
        
        # 解析JSON响应
        try:
            analysis_results = json.loads(response.content)
            return analysis_results
        except json.JSONDecodeError:
            logger.warning("千问返回非JSON格式，返回原始文本")
            return [{"raw_response": response.content}]
    
    async def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            模型信息字典
        """
        return {
            "model": self.model,
            "api_base": self.base_url,
            "max_tokens": 8192,  # 千问模型的最大Token数
            "pricing": self.token_prices.get(self.model),
            "capabilities": [
                "chat_completion",
                "batch_processing", 
                "json_output",
                "chinese_optimized"
            ]
        }

# 全局客户端实例（便捷使用）
_global_client: Optional[QwenLLMClient] = None

def get_qwen_client() -> QwenLLMClient:
    """获取全局千问客户端实例"""
    global _global_client
    if _global_client is None:
        _global_client = QwenLLMClient()
    return _global_client

async def quick_analyze(content: str, analysis_type: str = "sentiment") -> QwenResponse:
    """快速分析接口"""
    async with get_qwen_client() as client:
        return await client.analyze_news_batch([{"title": "新闻标题", "content": content}]) 