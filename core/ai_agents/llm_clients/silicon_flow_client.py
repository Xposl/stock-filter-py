#!/usr/bin/env python3

"""
硅基流动API客户端
提供OpenAI兼容的接口，作为千问LLM的备用服务
"""

import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Optional

import aiohttp

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class SiliconFlowResponse:
    """硅基流动响应数据结构"""

    content: str
    token_usage: dict[str, int]
    model: str
    request_id: str
    success: bool = True
    error_message: Optional[str] = None


class SiliconFlowClient:
    """
    硅基流动API客户端
    提供OpenAI兼容的接口，作为千问的备用LLM服务
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "qwen-turbo",
        timeout: int = 30,
    ):
        """
        初始化硅基流动客户端

        Args:
            api_key: API密钥，默认从环境变量获取
            base_url: API基础URL
            model: 使用的模型名称
            timeout: 请求超时时间
        """
        self.api_key = api_key or os.getenv("SILICON_FLOW_API_KEY")
        self.base_url = base_url or os.getenv(
            "SILICON_FLOW_BASE_URL", "https://api.siliconflow.cn/v1"
        )
        self.model = model
        self.timeout = timeout

        if not self.api_key:
            raise ValueError("硅基流动API密钥未配置，请设置SILICON_FLOW_API_KEY环境变量")

        # HTTP会话配置
        self.session: Optional[aiohttp.ClientSession] = None
        self._session_timeout = aiohttp.ClientTimeout(total=timeout)

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(
            timeout=self._session_timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "InvestNote-AI-Agent/1.0",
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self.session:
            await self.session.close()

    def _build_request_data(
        self, messages: list[dict[str, str]], **kwargs
    ) -> dict[str, Any]:
        """构建硅基流动API请求数据"""
        return {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "stream": kwargs.get("stream", False),
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000),
            "top_p": kwargs.get("top_p", 0.9),
        }

    async def _make_request(self, data: dict[str, Any]) -> dict[str, Any]:
        """执行HTTP请求"""
        if not self.session:
            raise RuntimeError("客户端未正确初始化，请使用async with语句")

        url = f"{self.base_url.rstrip('/')}/chat/completions"

        try:
            async with self.session.post(url, json=data) as response:
                response_data = await response.json()

                if response.status != 200:
                    error_msg = response_data.get("error", {}).get(
                        "message", f"HTTP {response.status}"
                    )
                    raise Exception(f"硅基流动API调用失败: {error_msg}")

                return response_data

        except aiohttp.ClientError as e:
            logger.error(f"硅基流动API网络请求失败: {e}")
            raise Exception(f"网络请求失败: {str(e)}") from e
        except Exception as e:
            logger.error(f"硅基流动API请求异常: {e}")
            raise

    def _parse_response(self, response_data: dict[str, Any]) -> SiliconFlowResponse:
        """解析硅基流动API响应"""
        try:
            # 提取响应内容
            choices = response_data.get("choices", [])
            if not choices:
                raise ValueError("响应中没有choices字段")

            content = choices[0].get("message", {}).get("content", "")

            # 提取Token使用信息
            usage_data = response_data.get("usage", {})

            return SiliconFlowResponse(
                content=content,
                token_usage=usage_data,
                model=response_data.get("model", self.model),
                request_id=response_data.get("id", ""),
                success=True,
            )

        except Exception as e:
            logger.error(f"解析硅基流动响应失败: {e}")
            return SiliconFlowResponse(
                content="",
                token_usage={},
                model=self.model,
                request_id="",
                success=False,
                error_message=str(e),
            )

    async def chat_completions(
        self, messages: list[dict[str, str]], **kwargs
    ) -> SiliconFlowResponse:
        """
        OpenAI兼容的聊天完成接口

        Args:
            messages: 消息列表，格式：[{"role": "user", "content": "..."}]
            **kwargs: 其他参数

        Returns:
            SiliconFlowResponse: 包含响应内容和Token使用信息
        """
        request_start_time = time.time()

        try:
            # 构建请求数据
            request_data = self._build_request_data(messages, **kwargs)

            logger.info(
                f"硅基流动API请求: model={request_data['model']}, messages_count={len(messages)}"
            )

            # 执行请求
            response_data = await self._make_request(request_data)

            # 解析响应
            result = self._parse_response(response_data)

            # 记录成功调用
            request_time = time.time() - request_start_time
            tokens = result.token_usage.get("total_tokens", 0)
            logger.info(f"硅基流动API调用成功: tokens={tokens}, time={request_time:.2f}s")

            return result

        except Exception as e:
            logger.error(f"硅基流动API调用失败: {e}")
            return SiliconFlowResponse(
                content="",
                token_usage={},
                model=self.model,
                request_id="",
                success=False,
                error_message=str(e),
            )

    async def analyze_news(
        self, news_content: str, analysis_type: str = "sentiment"
    ) -> SiliconFlowResponse:
        """
        新闻分析专用接口

        Args:
            news_content: 新闻内容
            analysis_type: 分析类型 (sentiment/investment/summary)

        Returns:
            SiliconFlowResponse: 分析结果
        """
        # 使用与千问客户端相同的prompt构建逻辑
        prompts = {
            "sentiment": self._build_sentiment_prompt(news_content),
            "investment": self._build_investment_prompt(news_content),
            "summary": self._build_summary_prompt(news_content),
        }

        if analysis_type not in prompts:
            raise ValueError(f"不支持的分析类型: {analysis_type}")

        messages = [{"role": "user", "content": prompts[analysis_type]}]

        return await self.chat_completions(
            messages=messages, model=self.model, temperature=0.3, max_tokens=800
        )

    def _build_sentiment_prompt(self, news_content: str) -> str:
        """构建情感分析Prompt"""
        return f"""请分析以下新闻的投资情感和市场影响：

新闻内容：
{news_content[:1000]}

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

    async def test_connection(self) -> bool:
        """测试连接"""
        try:
            test_message = [{"role": "user", "content": "你好，请回复'连接正常'"}]
            response = await self.chat_completions(test_message, max_tokens=10)
            return response.success and "连接正常" in response.content
        except Exception as e:
            logger.error(f"硅基流动连接测试失败: {e}")
            return False


# 全局客户端实例
_global_silicon_client: Optional[SiliconFlowClient] = None


def get_silicon_flow_client(model: str = "qwen-turbo") -> SiliconFlowClient:
    """获取全局硅基流动客户端实例"""
    global _global_silicon_client
    if _global_silicon_client is None or _global_silicon_client.model != model:
        _global_silicon_client = SiliconFlowClient(model=model)
    return _global_silicon_client
