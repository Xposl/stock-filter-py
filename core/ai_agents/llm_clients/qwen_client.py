#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
千问LLM客户端
提供OpenAI兼容的接口，用于新闻分析和AI处理
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import os
import aiohttp
from dataclasses import dataclass

# 配置日志
logger = logging.getLogger(__name__)

@dataclass
class TokenUsage:
    """Token使用统计"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_yuan: float
    request_time: datetime

@dataclass
class QwenResponse:
    """千问响应数据结构"""
    content: str
    token_usage: TokenUsage
    model: str
    request_id: str
    success: bool = True
    error_message: Optional[str] = None

class TokenCalculator:
    """Token计算器和成本监控"""
    
    # 千问模型价格（元/千token）
    QWEN_PRICING = {
        "qwen-turbo": {"input": 0.003, "output": 0.006},
        "qwen-plus": {"input": 0.008, "output": 0.016},
        "qwen-max": {"input": 0.02, "output": 0.04},
        "qwen-max-longcontext": {"input": 0.02, "output": 0.04}
    }
    
    def __init__(self):
        self.daily_usage: Dict[str, TokenUsage] = {}
        self.daily_limit = int(os.getenv('MAX_DAILY_TOKENS', '1000000'))
    
    def calculate_tokens(self, text: str) -> int:
        """简单Token计算（中文约1.5字符=1token）"""
        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
        english_chars = len([c for c in text if c.isalpha()])
        other_chars = len(text) - chinese_chars - english_chars
        
        # 中文：1.5字符≈1token，英文：4字符≈1token
        estimated_tokens = int(chinese_chars / 1.5 + english_chars / 4 + other_chars / 2)
        return max(estimated_tokens, 1)
    
    def calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """计算API调用成本"""
        if model not in self.QWEN_PRICING:
            model = "qwen-turbo"  # 默认使用最便宜的模型
        
        pricing = self.QWEN_PRICING[model]
        cost = (prompt_tokens * pricing["input"] + completion_tokens * pricing["output"]) / 1000
        return round(cost, 6)
    
    def check_daily_limit(self) -> bool:
        """检查是否超过日限额"""
        today = datetime.now().strftime('%Y-%m-%d')
        if today not in self.daily_usage:
            return True
        
        total_tokens = sum(usage.total_tokens for usage in self.daily_usage[today])
        return total_tokens < self.daily_limit
    
    def record_usage(self, usage: TokenUsage):
        """记录Token使用"""
        today = datetime.now().strftime('%Y-%m-%d')
        if today not in self.daily_usage:
            self.daily_usage[today] = []
        self.daily_usage[today].append(usage)
    
    def get_daily_stats(self) -> Dict[str, Any]:
        """获取今日使用统计"""
        today = datetime.now().strftime('%Y-%m-%d')
        if today not in self.daily_usage:
            return {"total_tokens": 0, "total_cost": 0.0, "request_count": 0}
        
        usages = self.daily_usage[today]
        return {
            "total_tokens": sum(u.total_tokens for u in usages),
            "total_cost": sum(u.cost_yuan for u in usages),
            "request_count": len(usages),
            "remaining_tokens": self.daily_limit - sum(u.total_tokens for u in usages)
        }

class QwenLLMClient:
    """
    千问LLM客户端
    提供OpenAI兼容的接口用于AI分析
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 model: str = "qwen-turbo",
                 timeout: int = 30):
        """
        初始化千问客户端
        
        Args:
            api_key: API密钥，默认从环境变量获取
            base_url: API基础URL
            model: 使用的模型名称
            timeout: 请求超时时间
        """
        self.api_key = api_key or os.getenv('QWEN_API_KEY')
        self.base_url = base_url or os.getenv('QWEN_BASE_URL', 'https://dashscope.aliyuncs.com/api/v1')
        self.model = model
        self.timeout = timeout
        
        if not self.api_key:
            raise ValueError("千问API密钥未配置，请设置QWEN_API_KEY环境变量")
        
        # Token计算器和成本监控
        self.token_calculator = TokenCalculator()
        
        # HTTP会话配置
        self.session: Optional[aiohttp.ClientSession] = None
        self._session_timeout = aiohttp.ClientTimeout(total=timeout)
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=self._session_timeout,
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'InvestNote-AI-Agent/1.0'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.session:
            await self.session.close()
    
    def _build_request_data(self, 
                           messages: List[Dict[str, str]], 
                           **kwargs) -> Dict[str, Any]:
        """构建千问API请求数据"""
        return {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "stream": kwargs.get("stream", False),
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000),
            "top_p": kwargs.get("top_p", 0.9),
            "repetition_penalty": kwargs.get("repetition_penalty", 1.1)
        }
    
    async def _make_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """执行HTTP请求"""
        if not self.session:
            raise RuntimeError("客户端未正确初始化，请使用async with语句")
        
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        
        try:
            async with self.session.post(url, json=data) as response:
                response_data = await response.json()
                
                if response.status != 200:
                    error_msg = response_data.get('error', {}).get('message', f'HTTP {response.status}')
                    raise Exception(f"千问API调用失败: {error_msg}")
                
                return response_data
        
        except aiohttp.ClientError as e:
            logger.error(f"千问API网络请求失败: {e}")
            raise Exception(f"网络请求失败: {str(e)}")
        except Exception as e:
            logger.error(f"千问API请求异常: {e}")
            raise
    
    def _parse_response(self, response_data: Dict[str, Any], request_start_time: float) -> QwenResponse:
        """解析千问API响应"""
        try:
            # 提取响应内容
            choices = response_data.get('choices', [])
            if not choices:
                raise ValueError("响应中没有choices字段")
            
            content = choices[0].get('message', {}).get('content', '')
            
            # 提取Token使用信息
            usage_data = response_data.get('usage', {})
            prompt_tokens = usage_data.get('prompt_tokens', 0)
            completion_tokens = usage_data.get('completion_tokens', 0)
            total_tokens = usage_data.get('total_tokens', prompt_tokens + completion_tokens)
            
            # 计算成本
            model = response_data.get('model', self.model)
            cost = self.token_calculator.calculate_cost(model, prompt_tokens, completion_tokens)
            
            # 创建Token使用记录
            token_usage = TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost_yuan=cost,
                request_time=datetime.now()
            )
            
            # 记录使用统计
            self.token_calculator.record_usage(token_usage)
            
            return QwenResponse(
                content=content,
                token_usage=token_usage,
                model=model,
                request_id=response_data.get('id', ''),
                success=True
            )
        
        except Exception as e:
            logger.error(f"解析千问响应失败: {e}")
            return QwenResponse(
                content='',
                token_usage=TokenUsage(0, 0, 0, 0.0, datetime.now()),
                model=self.model,
                request_id='',
                success=False,
                error_message=str(e)
            )
    
    async def chat_completions(self, 
                              messages: List[Dict[str, str]], 
                              **kwargs) -> QwenResponse:
        """
        OpenAI兼容的聊天完成接口
        
        Args:
            messages: 消息列表，格式：[{"role": "user", "content": "..."}]
            **kwargs: 其他参数
        
        Returns:
            QwenResponse: 包含响应内容和Token使用信息
        """
        # 检查日限额
        if not self.token_calculator.check_daily_limit():
            logger.warning("今日Token使用量已达上限")
            return QwenResponse(
                content='',
                token_usage=TokenUsage(0, 0, 0, 0.0, datetime.now()),
                model=self.model,
                request_id='',
                success=False,
                error_message="今日Token使用量已达上限"
            )
        
        request_start_time = time.time()
        
        try:
            # 构建请求数据
            request_data = self._build_request_data(messages, **kwargs)
            
            logger.info(f"千问API请求: model={request_data['model']}, messages_count={len(messages)}")
            
            # 执行请求
            response_data = await self._make_request(request_data)
            
            # 解析响应
            result = self._parse_response(response_data, request_start_time)
            
            # 记录成功调用
            request_time = time.time() - request_start_time
            logger.info(f"千问API调用成功: tokens={result.token_usage.total_tokens}, "
                       f"cost={result.token_usage.cost_yuan:.6f}元, time={request_time:.2f}s")
            
            return result
        
        except Exception as e:
            logger.error(f"千问API调用失败: {e}")
            return QwenResponse(
                content='',
                token_usage=TokenUsage(0, 0, 0, 0.0, datetime.now()),
                model=self.model,
                request_id='',
                success=False,
                error_message=str(e)
            )
    
    async def analyze_news(self, 
                          news_content: str, 
                          analysis_type: str = "sentiment") -> QwenResponse:
        """
        新闻分析专用接口
        
        Args:
            news_content: 新闻内容
            analysis_type: 分析类型 (sentiment/investment/summary)
        
        Returns:
            QwenResponse: 分析结果
        """
        # 根据分析类型构建不同的prompt
        prompts = {
            "sentiment": self._build_sentiment_prompt(news_content),
            "investment": self._build_investment_prompt(news_content),
            "summary": self._build_summary_prompt(news_content)
        }
        
        if analysis_type not in prompts:
            raise ValueError(f"不支持的分析类型: {analysis_type}")
        
        messages = [{"role": "user", "content": prompts[analysis_type]}]
        
        return await self.chat_completions(
            messages=messages,
            model=self.model,
            temperature=0.3,  # 分析任务使用较低的温度
            max_tokens=800
        )
    
    def _build_sentiment_prompt(self, news_content: str) -> str:
        """构建情感分析Prompt"""
        return f"""请分析以下新闻的投资情感和市场影响：

新闻内容：
{news_content[:1000]}  # 限制长度控制Token

请从以下维度进行分析，并以JSON格式返回：
1. 情感评分：-10到10，负数表示负面，正数表示正面
2. 市场影响度：1-10，数字越大影响越大
3. 主要关键词：提取3-5个关键词
4. 影响的行业：相关行业列表
5. 风险等级：低/中/高

返回格式：
{{
  "sentiment_score": 数字,
  "market_impact": 数字,
  "keywords": ["关键词1", "关键词2"],
  "affected_industries": ["行业1", "行业2"],
  "risk_level": "低/中/高",
  "summary": "简要总结"
}}"""
    
    def _build_investment_prompt(self, news_content: str) -> str:
        """构建投资建议Prompt"""
        return f"""请基于以下新闻内容提供投资建议：

新闻内容：
{news_content[:1000]}

请提供具体的投资建议，以JSON格式返回：
1. 投资建议：买入/持有/卖出/观望
2. 推荐股票：相关股票代码或行业
3. 时间窗口：短期/中期/长期
4. 风险提示：主要风险点
5. 信心度：1-10，数字越大信心越足

返回格式：
{{
  "investment_advice": "买入/持有/卖出/观望",
  "recommended_stocks": ["股票代码或行业"],
  "time_horizon": "短期/中期/长期",
  "risk_warning": "风险提示内容",
  "confidence_level": 数字,
  "rationale": "投资逻辑"
}}"""
    
    def _build_summary_prompt(self, news_content: str) -> str:
        """构建摘要提取Prompt"""
        return f"""请对以下新闻进行摘要提取：

新闻内容：
{news_content}

请提供简洁的摘要，以JSON格式返回：
1. 核心要点：3-5个要点
2. 关键数据：重要的数字和比例
3. 涉及公司：相关公司名称
4. 时间信息：重要的时间节点

返回格式：
{{
  "key_points": ["要点1", "要点2", "要点3"],
  "key_data": ["数据1", "数据2"],
  "companies": ["公司1", "公司2"],
  "time_info": ["时间1", "时间2"],
  "summary": "一句话总结"
}}"""
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """获取使用统计"""
        daily_stats = self.token_calculator.get_daily_stats()
        return {
            "daily_stats": daily_stats,
            "model": self.model,
            "daily_limit": self.token_calculator.daily_limit
        }
    
    async def test_connection(self) -> bool:
        """测试连接"""
        try:
            test_message = [{"role": "user", "content": "你好，请回复'连接正常'"}]
            response = await self.chat_completions(test_message, max_tokens=10)
            return response.success and "连接正常" in response.content
        except Exception as e:
            logger.error(f"千问连接测试失败: {e}")
            return False

# 全局客户端实例（便捷使用）
_global_client: Optional[QwenLLMClient] = None

def get_qwen_client(model: str = "qwen-turbo") -> QwenLLMClient:
    """获取全局千问客户端实例"""
    global _global_client
    if _global_client is None or _global_client.model != model:
        _global_client = QwenLLMClient(model=model)
    return _global_client

async def quick_analyze(content: str, analysis_type: str = "sentiment") -> QwenResponse:
    """快速分析接口"""
    async with get_qwen_client() as client:
        return await client.analyze_news(content, analysis_type) 