#!/usr/bin/env python3

"""
新闻分析流水线 (重构版)

基于PocketFlow框架的多Agent协作新闻分析系统。
重构后的版本使用独立的节点文件，提高代码组织性和可维护性。
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ...models.news_article import NewsArticle

# 项目内部模块导入
from ..llm_clients.qwen_client import QwenLLMClient

# 重构后的节点导入
from ..nodes.analysis.news_classifier_node import NewsClassifierNode
from ..nodes.analysis.stock_analyzer_node import StockAnalyzerNode
from ..nodes.decision.investment_advisor_node import InvestmentAdvisorNode

logger = logging.getLogger(__name__)


@dataclass
class EnhancedNewsAnalysisResult:
    """新闻分析结果 - 保持与原版一致"""

    news_id: str
    article: NewsArticle  # 使用真实的NewsArticle对象
    analysis_type: str  # "stock_specific" 或 "industry_focused"
    mentioned_stocks: list[dict[str, Any]]  # 新闻中提到的具体股票
    classification: dict[str, Any]
    industry_analysis: dict[str, Any]
    related_stocks: list[dict[str, Any]]  # 高评分相关股票
    investment_advice: dict[str, Any]
    analysis_time: datetime
    confidence_score: float
    processing_time: float


class NewsAnalysisFlow:
    """新闻分析流水线主类 - 重构版，专注流程编排"""

    def __init__(self, llm_client: QwenLLMClient, test_mode: bool = False):
        """
        初始化新闻分析流水线

        Args:
            llm_client: 千问LLM客户端
            test_mode: 是否为测试模式，避免数据库连接
        """
        self.llm_client = llm_client
        self.test_mode = test_mode

        # 🔄 使用重构后的独立节点，传递测试模式标志
        self.classifier_node = NewsClassifierNode(self.llm_client, test_mode=test_mode)
        self.stock_analyzer_node = StockAnalyzerNode(self.llm_client)
        self.advisor_node = InvestmentAdvisorNode(self.llm_client)

        if test_mode:
            logger.info("🧪 新闻分析流水线已初始化 (测试模式，无数据库连接)")
        else:
            logger.info("🏗️ 新闻分析流水线已初始化 (生产模式)")

    def analyze_news_with_article(
        self, article: NewsArticle
    ) -> EnhancedNewsAnalysisResult:
        """
        分析NewsArticle对象 - 保持与原版接口一致

        Args:
            article: NewsArticle模型对象

        Returns:
            新闻分析结果
        """
        # 检查是否在运行中的事件循环中
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                # 在运行中的事件循环中，使用同步调用异步方法的方式
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, self.analyze_news_with_article_async(article)
                    )
                    return future.result()
        except RuntimeError:
            # 没有运行中的事件循环，可以直接使用asyncio.run
            pass

        return asyncio.run(self.analyze_news_with_article_async(article))

    async def analyze_news_with_article_async(
        self, article: NewsArticle
    ) -> EnhancedNewsAnalysisResult:
        """
        分析NewsArticle对象 - 异步版本，保持原有逻辑

        Args:
            article: NewsArticle模型对象

        Returns:
            新闻分析结果
        """
        start_time = datetime.now()

        # 初始化共享存储，传入真实的NewsArticle对象
        shared_store = {"article": article, "start_time": start_time}

        try:
            # 🔄 第一步：新闻分类 (使用重构后的节点)
            classifier_prep = self.classifier_node.prep(shared_store)
            classifier_result = self.classifier_node.work(classifier_prep)
            action = self.classifier_node.post(
                shared_store, classifier_prep, classifier_result
            )

            if action == "error":
                raise Exception(f"分类失败: {shared_store.get('error', '未知错误')}")

            # 🔄 第二步：根据分析类型执行股票分析 (使用重构后的节点)
            if action in ["analyze_stocks", "analyze_industry"]:
                stock_prep = self.stock_analyzer_node.prep(shared_store)
                stock_result = await self.stock_analyzer_node._exec_async(stock_prep)
                action = self.stock_analyzer_node.post(
                    shared_store, stock_prep, stock_result
                )

                if action == "error":
                    raise Exception(f"股票分析失败: {shared_store.get('error', '未知错误')}")

            # 🔄 第三步：生成投资建议 (使用重构后的节点)
            if action == "generate_advice":
                advisor_prep = self.advisor_node.prep(shared_store)
                advisor_result = await self.advisor_node._exec_async(advisor_prep)
                self.advisor_node.post(shared_store, advisor_prep, advisor_result)

            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()

            # 计算信心评分
            confidence_score = self._calculate_confidence_score(shared_store)

            # 🔄 构建结果对象 (保持与原版一致的结构)
            result = EnhancedNewsAnalysisResult(
                news_id=str(article.id),
                article=article,
                analysis_type=shared_store.get("analysis_type", "industry_focused"),
                mentioned_stocks=shared_store.get("mentioned_stocks", []),
                classification=shared_store.get("classification", {}),
                industry_analysis=shared_store.get("industry_analysis", {}),
                related_stocks=shared_store.get("related_stocks", []),
                investment_advice=shared_store.get("investment_advice", {}),
                analysis_time=start_time,
                confidence_score=confidence_score,
                processing_time=processing_time,
            )

            logger.info(f"✅ 新闻分析完成 (重构版): {article.id}, 耗时: {processing_time:.2f}秒")
            return result

        except Exception as e:
            logger.error(f"❌ 新闻分析流水线执行失败 (重构版): {e}")
            # 返回错误结果
            return EnhancedNewsAnalysisResult(
                news_id=str(article.id),
                article=article,
                analysis_type="industry_focused",
                mentioned_stocks=[],
                classification={},
                industry_analysis={},
                related_stocks=[],
                investment_advice={
                    "recommendation": "观望",
                    "rationale": f"分析失败: {str(e)}",
                },
                analysis_time=start_time,
                confidence_score=0.0,
                processing_time=(datetime.now() - start_time).total_seconds(),
            )

    def analyze_news(
        self, news_content: str, news_id: str = None
    ) -> EnhancedNewsAnalysisResult:
        """
        分析单条新闻内容（向后兼容）- 保持与原版接口一致

        Args:
            news_content: 新闻内容
            news_id: 新闻ID（可选）

        Returns:
            新闻分析结果
        """
        # 创建临时NewsArticle对象
        temp_article = NewsArticle(
            id=int(news_id) if news_id and news_id.isdigit() else 0,
            title=news_content[:100] + "..."
            if len(news_content) > 100
            else news_content,
            url="",
            url_hash="",
            content=news_content,
            source_id=0,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        return self.analyze_news_with_article(temp_article)

    def _calculate_confidence_score(self, shared_store: dict[str, Any]) -> float:
        """计算分析结果的信心评分 - 保持与原版一致的逻辑"""
        try:
            # 基础分数
            base_score = 0.5

            # 分类质量评分
            classification = shared_store.get("classification", {})
            if classification.get("importance_score", 0) >= 7:
                base_score += 0.2

            # 行业分析质量评分
            industry_analysis = shared_store.get("industry_analysis", {})
            affected_industries = industry_analysis.get("affected_industries", [])
            if len(affected_industries) > 0:
                avg_impact = sum(
                    ind.get("impact_degree", 0) for ind in affected_industries
                ) / len(affected_industries)
                if avg_impact >= 7:
                    base_score += 0.2

            # 股票关联质量评分
            related_stocks = shared_store.get("related_stocks", [])
            if len(related_stocks) >= 3:
                base_score += 0.1

            # 投资建议质量评分
            investment_advice = shared_store.get("investment_advice", {})
            advice_confidence = investment_advice.get("confidence_level", 0)
            if advice_confidence >= 7:
                base_score += 0.2

            return min(1.0, base_score)

        except Exception as e:
            logger.error(f"计算信心评分失败: {e}")
            return 0.5


# 🔄 便捷函数 - 保持与原版接口一致
def analyze_single_news(
    news_content: str, news_id: str = None, test_mode: bool = False
) -> EnhancedNewsAnalysisResult:
    """
    快速分析单条新闻的便捷函数 - 使用重构后的流程

    Args:
        news_content: 新闻内容
        news_id: 新闻ID（可选）
        test_mode: 是否为测试模式，避免数据库连接

    Returns:
        新闻分析结果
    """
    # 临时创建客户端
    qwen_client = QwenLLMClient()
    analysis_flow = NewsAnalysisFlow(qwen_client, test_mode)

    return analysis_flow.analyze_news(news_content, news_id)
