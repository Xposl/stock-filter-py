#!/usr/bin/env python3

"""
新闻聚合管理器
统一管理各种新闻源的抓取和处理
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

import aiohttp

from ..models.news_article import NewsArticleCreate
from ..models.news_source import NewsSource, NewsSourceStatus, NewsSourceType
from ..service.news_article_repository import NewsArticleRepository

# 使用Repository模式替代SQLAlchemy查询
from ..service.news_source_repository import NewsSourceRepository
from .rss_aggregator import RSSAggregator
from .xueqiu_aggregator import XueqiuAggregator

logger = logging.getLogger(__name__)


class NewsAggregatorManager:
    """新闻聚合管理器"""

    def __init__(self):
        """初始化新闻聚合管理器"""
        self.news_source_repo = NewsSourceRepository()
        self.news_article_repo = NewsArticleRepository()

        # 共享的HTTP会话，避免并发冲突
        self._shared_session = None

        # 注册聚合器
        self.aggregators = {
            NewsSourceType.RSS: RSSAggregator,
            NewsSourceType.API: XueqiuAggregator,  # 雪球API
        }

        logger.info("新闻聚合管理器初始化完成")

    async def _ensure_shared_session(self):
        """确保有共享的HTTP会话"""
        if self._shared_session is None or self._shared_session.closed:
            # 创建连接器，优化并发性能
            connector = aiohttp.TCPConnector(
                limit=100,  # 总连接池大小
                limit_per_host=20,  # 单host连接池大小
                ssl=False,  # 处理SSL证书问题
                keepalive_timeout=30,  # 保持连接30秒
                enable_cleanup_closed=True,  # 自动清理关闭的连接
            )

            # 设置超时
            timeout = aiohttp.ClientTimeout(total=60, connect=10)

            # 创建共享会话
            self._shared_session = aiohttp.ClientSession(
                connector=connector, timeout=timeout
            )
            logger.info("创建共享HTTP会话")

    async def _close_shared_session(self):
        """关闭共享的HTTP会话"""
        if self._shared_session and not self._shared_session.closed:
            await self._shared_session.close()
            logger.info("共享HTTP会话已关闭")

    async def fetch_all_active_sources(self) -> list[dict[str, Any]]:
        """
        抓取所有活跃新闻源的数据

        Returns:
            抓取结果汇总
        """
        results = []

        try:
            # 确保共享会话可用
            await self._ensure_shared_session()

            # 使用Repository获取所有活跃的新闻源
            active_sources = await self.news_source_repo.get_news_sources_by_status(
                NewsSourceStatus.ACTIVE
            )

            logger.info(f"发现 {len(active_sources)} 个活跃新闻源")

            # 并发抓取所有源
            tasks = []
            for source in active_sources:
                task = asyncio.create_task(self._fetch_single_source(source))
                tasks.append(task)

            # 等待所有任务完成
            fetch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果
            for i, result in enumerate(fetch_results):
                source = active_sources[i]
                if isinstance(result, Exception):
                    logger.error(f"抓取新闻源失败 {source.name}: {result}")
                    await self._update_source_error_status(source, str(result))
                    results.append(
                        {
                            "source_name": source.name,
                            "source_id": source.id,
                            "status": "error",
                            "error": str(result),
                            "articles_count": 0,
                        }
                    )
                else:
                    articles_count = len(result)
                    logger.info(f"新闻源 {source.name} 抓取完成: {articles_count} 篇文章")
                    await self._update_source_success_status(source, articles_count)
                    results.append(
                        {
                            "source_name": source.name,
                            "source_id": source.id,
                            "status": "success",
                            "articles_count": articles_count,
                            "articles": result,
                        }
                    )

        finally:
            # 保持会话开放，由外部管理生命周期
            pass

        return results

    async def fetch_specific_sources(
        self, source_ids: list[int]
    ) -> list[dict[str, Any]]:
        """
        抓取指定的新闻源

        Args:
            source_ids: 新闻源ID列表

        Returns:
            抓取结果汇总
        """
        results = []

        try:
            # 确保共享会话可用
            await self._ensure_shared_session()

            # 使用Repository获取指定的新闻源
            sources = []
            for source_id in source_ids:
                source = await self.news_source_repo.get_news_source_by_id(source_id)
                if source:
                    sources.append(source)
                else:
                    logger.warning(f"新闻源不存在: {source_id}")

            logger.info(f"开始抓取 {len(sources)} 个指定新闻源")

            # 并发抓取
            tasks = []
            for source in sources:
                task = asyncio.create_task(self._fetch_single_source(source))
                tasks.append(task)

            fetch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果
            for i, result in enumerate(fetch_results):
                source = sources[i]
                if isinstance(result, Exception):
                    logger.error(f"抓取新闻源失败 {source.name}: {result}")
                    results.append(
                        {
                            "source_name": source.name,
                            "source_id": source.id,
                            "status": "error",
                            "error": str(result),
                            "articles_count": 0,
                        }
                    )
                else:
                    results.append(
                        {
                            "source_name": source.name,
                            "source_id": source.id,
                            "status": "success",
                            "articles_count": len(result),
                            "articles": result,
                        }
                    )

        finally:
            # 保持会话开放，由外部管理生命周期
            pass

        return results

    async def _fetch_single_source(
        self, news_source: NewsSource
    ) -> list[dict[str, Any]]:
        """
        抓取单个新闻源

        Args:
            news_source: 新闻源配置

        Returns:
            文章数据列表
        """
        logger.info(f"开始抓取新闻源: {news_source.name} ({news_source.source_type})")

        # 根据源类型选择对应的聚合器
        aggregator_class = self.aggregators.get(news_source.source_type)
        if not aggregator_class:
            raise ValueError(f"不支持的新闻源类型: {news_source.source_type}")

        # 创建聚合器实例并抓取数据，使用共享会话
        if news_source.source_type == NewsSourceType.API:
            # 雪球聚合器使用共享会话
            aggregator = aggregator_class(session=self._shared_session)
        else:
            # RSS聚合器不需要共享会话
            aggregator = aggregator_class()

        # 使用聚合器的上下文管理器
        async with aggregator:
            if news_source.source_type == NewsSourceType.RSS:
                articles = await aggregator.fetch_rss_feed(news_source)
            elif news_source.source_type == NewsSourceType.API:
                # 目前API类型主要是雪球
                articles = await aggregator.fetch_xueqiu_timeline(news_source)
            else:
                raise ValueError(f"未实现的新闻源类型处理: {news_source.source_type}")

        # 保存文章到数据库
        if articles:
            await self._save_articles_to_db(articles)

        return articles

    async def _save_articles_to_db(self, articles: list[dict[str, Any]]):
        """
        保存文章到数据库

        Args:
            articles: 文章数据列表
        """
        if not articles:
            return

        logger.info(f"开始保存 {len(articles)} 篇文章到数据库")

        saved_count = 0

        for article_data in articles:
            try:
                # 检查是否已存在（根据URL哈希去重）
                url_hash = article_data.get("url_hash")
                if url_hash:
                    existing = await self.news_article_repo.get_article_by_url_hash(
                        url_hash
                    )
                    if existing:
                        logger.debug(f"文章已存在，跳过: {article_data.get('title', '')[:50]}")
                        continue

                # 创建新文章记录
                article_create = NewsArticleCreate(**article_data)
                article = await self.news_article_repo.create_news_article(
                    article_create
                )
                if article:
                    saved_count += 1

            except Exception as e:
                logger.error(f"保存文章失败: {e}", exc_info=True)
                continue

        logger.info(f"成功保存 {saved_count} 篇新文章到数据库")

    async def _update_source_success_status(
        self, news_source: NewsSource, articles_count: int
    ):
        """更新新闻源成功状态"""
        try:
            await self.news_source_repo.update_last_fetch_info(
                news_source.id, error_message=None, article_count=articles_count
            )
        except Exception as e:
            logger.error(f"更新新闻源状态失败: {e}")

    async def _update_source_error_status(
        self, news_source: NewsSource, error_message: str
    ):
        """更新新闻源错误状态"""
        try:
            await self.news_source_repo.update_last_fetch_info(
                news_source.id, error_message=error_message, article_count=0
            )
        except Exception as e:
            logger.error(f"更新新闻源错误状态失败: {e}")

    async def get_aggregation_stats(self) -> dict[str, Any]:
        """
        获取聚合统计信息

        Returns:
            统计信息字典
        """
        try:
            # 获取新闻源统计
            source_stats = await self.news_source_repo.get_news_source_stats()

            # 获取文章统计
            article_stats = await self.news_article_repo.get_article_stats()

            return {
                "sources": source_stats,
                "articles": article_stats,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"获取聚合统计失败: {e}")
            return {
                "sources": {},
                "articles": {},
                "error": str(e),
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }

    async def test_source_connectivity(self, source_id: int) -> dict[str, Any]:
        """
        测试新闻源连接性

        Args:
            source_id: 新闻源ID

        Returns:
            测试结果
        """
        try:
            # 确保共享会话可用
            await self._ensure_shared_session()

            # 获取新闻源
            news_source = await self.news_source_repo.get_news_source_by_id(source_id)
            if not news_source:
                return {
                    "success": False,
                    "error": f"新闻源不存在: {source_id}",
                    "test_time": datetime.now(timezone.utc).isoformat(),
                }

            # 测试连接
            aggregator_class = self.aggregators.get(news_source.source_type)
            if not aggregator_class:
                return {
                    "success": False,
                    "error": f"不支持的新闻源类型: {news_source.source_type}",
                    "test_time": datetime.now(timezone.utc).isoformat(),
                }

            # 进行实际连接测试
            start_time = datetime.now()

            # 创建聚合器实例，使用共享会话
            if news_source.source_type == NewsSourceType.API:
                aggregator = aggregator_class(session=self._shared_session)
            else:
                aggregator = aggregator_class()

            async with aggregator:
                if news_source.source_type == NewsSourceType.RSS:
                    test_articles = await aggregator.fetch_rss_feed(news_source)
                elif news_source.source_type == NewsSourceType.API:
                    test_articles = await aggregator.fetch_xueqiu_timeline(news_source)
                else:
                    raise ValueError(f"未实现的测试类型: {news_source.source_type}")

            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()

            return {
                "success": True,
                "source_name": news_source.name,
                "source_type": news_source.source_type.value,
                "response_time_seconds": response_time,
                "test_articles_count": len(test_articles) if test_articles else 0,
                "test_time": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"新闻源连接测试失败 {source_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "test_time": datetime.now(timezone.utc).isoformat(),
            }

    async def cleanup(self):
        """清理资源"""
        try:
            await self._close_shared_session()
            logger.info("新闻聚合管理器资源清理完成")
        except Exception as e:
            logger.error(f"清理新闻聚合管理器资源失败: {e}")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._ensure_shared_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.cleanup()


# 工厂函数（兼容原有接口）
async def create_news_aggregator_manager() -> NewsAggregatorManager:
    """
    创建新闻聚合管理器实例

    Returns:
        新闻聚合管理器实例
    """
    return NewsAggregatorManager()
