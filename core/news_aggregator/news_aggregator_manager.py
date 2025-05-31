"""
新闻聚合管理器
统一管理不同类型的新闻聚合器（RSS、API等）
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update

from ..models.news_source import NewsSource, NewsSourceType, NewsSourceStatus
from ..models.news_article import NewsArticle, ArticleStatus
from .rss_aggregator import RSSAggregator
from .xueqiu_aggregator import XueqiuAggregator

logger = logging.getLogger(__name__)

class NewsAggregatorManager:
    """新闻聚合管理器"""
    
    def __init__(self, session_factory: sessionmaker):
        """
        初始化聚合管理器
        
        Args:
            session_factory: 数据库会话工厂
        """
        self.session_factory = session_factory
        self.aggregators = {
            NewsSourceType.RSS: RSSAggregator,
            NewsSourceType.API: XueqiuAggregator,  # 目前API类型主要用于雪球
        }
    
    async def fetch_all_active_sources(self) -> List[Dict[str, Any]]:
        """
        抓取所有活跃新闻源的数据
        
        Returns:
            抓取结果汇总
        """
        results = []
        
        async with self.session_factory() as session:
            # 获取所有活跃的新闻源
            query = select(NewsSource).where(NewsSource.status == NewsSourceStatus.ACTIVE)
            result = await session.execute(query)
            active_sources = result.scalars().all()
        
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
                results.append({
                    'source_name': source.name,
                    'source_id': source.id,
                    'status': 'error',
                    'error': str(result),
                    'articles_count': 0
                })
            else:
                articles_count = len(result)
                logger.info(f"新闻源 {source.name} 抓取完成: {articles_count} 篇文章")
                await self._update_source_success_status(source, articles_count)
                results.append({
                    'source_name': source.name,
                    'source_id': source.id,
                    'status': 'success',
                    'articles_count': articles_count,
                    'articles': result
                })
        
        return results
    
    async def fetch_specific_sources(self, source_ids: List[int]) -> List[Dict[str, Any]]:
        """
        抓取指定的新闻源
        
        Args:
            source_ids: 新闻源ID列表
            
        Returns:
            抓取结果汇总
        """
        results = []
        
        async with self.session_factory() as session:
            # 获取指定的新闻源
            query = select(NewsSource).where(NewsSource.id.in_(source_ids))
            result = await session.execute(query)
            sources = result.scalars().all()
        
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
                results.append({
                    'source_name': source.name,
                    'source_id': source.id,
                    'status': 'error',
                    'error': str(result),
                    'articles_count': 0
                })
            else:
                results.append({
                    'source_name': source.name,
                    'source_id': source.id,
                    'status': 'success',
                    'articles_count': len(result),
                    'articles': result
                })
        
        return results
    
    async def _fetch_single_source(self, news_source: NewsSource) -> List[Dict[str, Any]]:
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
        
        # 创建聚合器实例并抓取数据
        async with aggregator_class() as aggregator:
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
    
    async def _save_articles_to_db(self, articles: List[Dict[str, Any]]):
        """
        保存文章到数据库
        
        Args:
            articles: 文章数据列表
        """
        if not articles:
            return
        
        logger.info(f"开始保存 {len(articles)} 篇文章到数据库")
        
        async with self.session_factory() as session:
            saved_count = 0
            
            for article_data in articles:
                try:
                    # 检查是否已存在（根据URL哈希去重）
                    url_hash = article_data.get('url_hash')
                    if url_hash:
                        query = select(NewsArticle).where(NewsArticle.url_hash == url_hash)
                        result = await session.execute(query)
                        existing = result.scalar_one_or_none()
                        
                        if existing:
                            logger.debug(f"文章已存在，跳过: {article_data.get('title', '')[:50]}")
                            continue
                    
                    # 创建新文章记录
                    article = NewsArticle(**article_data)
                    session.add(article)
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"保存文章失败: {e}", exc_info=True)
                    continue
            
            # 提交所有更改
            await session.commit()
            logger.info(f"成功保存 {saved_count} 篇新文章到数据库")
    
    async def _update_source_success_status(self, news_source: NewsSource, articles_count: int):
        """更新新闻源成功状态"""
        async with self.session_factory() as session:
            query = (
                update(NewsSource)
                .where(NewsSource.id == news_source.id)
                .values(
                    last_fetch_time=datetime.now(timezone.utc),
                    last_error_message=None,
                    total_articles_fetched=NewsSource.total_articles_fetched + articles_count,
                    status=NewsSourceStatus.ACTIVE
                )
            )
            await session.execute(query)
            await session.commit()
    
    async def _update_source_error_status(self, news_source: NewsSource, error_message: str):
        """更新新闻源错误状态"""
        async with self.session_factory() as session:
            query = (
                update(NewsSource)
                .where(NewsSource.id == news_source.id)
                .values(
                    last_fetch_time=datetime.now(timezone.utc),
                    last_error_message=error_message,
                    status=NewsSourceStatus.ERROR
                )
            )
            await session.execute(query)
            await session.commit()
    
    async def get_aggregation_stats(self) -> Dict[str, Any]:
        """
        获取聚合统计信息
        
        Returns:
            统计信息字典
        """
        async with self.session_factory() as session:
            # 新闻源统计
            sources_query = select(NewsSource)
            sources_result = await session.execute(sources_query)
            all_sources = sources_result.scalars().all()
            
            source_stats = {
                'total': len(all_sources),
                'active': len([s for s in all_sources if s.status == NewsSourceStatus.ACTIVE]),
                'error': len([s for s in all_sources if s.status == NewsSourceStatus.ERROR]),
                'suspended': len([s for s in all_sources if s.status == NewsSourceStatus.SUSPENDED]),
                'inactive': len([s for s in all_sources if s.status == NewsSourceStatus.INACTIVE])
            }
            
            # 文章统计
            articles_query = select(NewsArticle)
            articles_result = await session.execute(articles_query)
            all_articles = articles_result.scalars().all()
            
            article_stats = {
                'total': len(all_articles),
                'pending': len([a for a in all_articles if a.status == ArticleStatus.PENDING]),
                'processed': len([a for a in all_articles if a.status == ArticleStatus.PROCESSED]),
                'failed': len([a for a in all_articles if a.status == ArticleStatus.FAILED]),
                'archived': len([a for a in all_articles if a.status == ArticleStatus.ARCHIVED])
            }
            
            # 最近抓取统计
            recent_sources = [s for s in all_sources if s.last_fetch_time]
            recent_sources.sort(key=lambda x: x.last_fetch_time, reverse=True)
            
            return {
                'source_stats': source_stats,
                'article_stats': article_stats,
                'recent_fetches': [
                    {
                        'name': s.name,
                        'last_fetch_time': s.last_fetch_time.isoformat() if s.last_fetch_time else None,
                        'total_articles': s.total_articles_fetched,
                        'status': s.status.value
                    }
                    for s in recent_sources[:10]  # 最近10次抓取
                ],
                'total_sources': len(all_sources),
                'total_articles': len(all_articles)
            }
    
    async def test_source_connectivity(self, source_id: int) -> Dict[str, Any]:
        """
        测试新闻源连通性
        
        Args:
            source_id: 新闻源ID
            
        Returns:
            测试结果
        """
        async with self.session_factory() as session:
            # 获取新闻源
            source = await session.get(NewsSource, source_id)
            if not source:
                return {
                    'success': False,
                    'error': '新闻源不存在'
                }
        
        try:
            # 尝试抓取少量数据进行测试
            original_max = source.max_articles_per_fetch
            source.max_articles_per_fetch = 3  # 临时设置为3篇用于测试
            
            articles = await self._fetch_single_source(source)
            
            return {
                'success': True,
                'articles_count': len(articles),
                'sample_articles': [
                    {
                        'title': article.get('title', '')[:100],
                        'url': article.get('url', ''),
                        'published_at': article.get('published_at')
                    }
                    for article in articles[:3]
                ]
            }
            
        except Exception as e:
            logger.error(f"测试新闻源连通性失败 {source.name}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            # 恢复原始设置
            source.max_articles_per_fetch = original_max

# 便捷函数
async def create_news_aggregator_manager(session_factory: sessionmaker) -> NewsAggregatorManager:
    """
    创建新闻聚合管理器的便捷函数
    
    Args:
        session_factory: 数据库会话工厂
        
    Returns:
        新闻聚合管理器实例
    """
    return NewsAggregatorManager(session_factory) 