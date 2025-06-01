"""
雪球新闻聚合器
专门处理雪球平台的投资动态和新闻数据
现在使用重构后的雪球客户端抽象层
"""

from typing import List, Dict, Optional, Any
import logging

from ..utils.xueqiu.xueqiu_client_factory import create_news_client
from ..models.news_source import NewsSource, NewsSourceType, NewsSourceStatus
from ..models.news_article import NewsArticle, ArticleStatus

logger = logging.getLogger(__name__)


class XueqiuAggregator:
    """雪球新闻聚合器 - 重构版本"""
    
    def __init__(self, session=None):
        """
        初始化雪球聚合器
        
        Args:
            session: 可选的aiohttp客户端会话（向后兼容）
        """
        self.session = session
        # 使用新的客户端工厂创建新闻客户端
        self._client = create_news_client(session)
        logger.info("雪球聚合器初始化完成（使用重构后的客户端）")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        # 确保客户端正确初始化
        if hasattr(self._client, '__aenter__'):
            await self._client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if hasattr(self._client, '__aexit__'):
            await self._client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def fetch_xueqiu_timeline(self, news_source: NewsSource) -> List[Dict[str, Any]]:
        """
        抓取雪球时间线数据
        
        Args:
            news_source: 新闻源配置
            
        Returns:
            新闻文章列表
        """
        try:
            logger.info(f"开始抓取雪球数据: {news_source.name}")
            
            # 使用重构后的客户端
            articles = await self._client.fetch_timeline_data(news_source)
            
            logger.info(f"成功抓取 {len(articles)} 篇雪球动态")
            return articles
            
        except Exception as e:
            logger.error(f"抓取雪球数据失败 {news_source.name}: {e}", exc_info=True)
            raise
    
    # 为了向后兼容，保留原有方法名
    async def fetch_xueqiu_timeline_data(self, news_source: NewsSource) -> List[Dict[str, Any]]:
        """向后兼容的方法名"""
        return await self.fetch_xueqiu_timeline(news_source)


# 向后兼容的函数
async def fetch_xueqiu_data(news_source: NewsSource) -> List[Dict[str, Any]]:
    """
    向后兼容的函数：抓取雪球数据
    
    Args:
        news_source: 新闻源配置
        
    Returns:
        新闻文章列表
    """
    async with XueqiuAggregator() as aggregator:
        return await aggregator.fetch_xueqiu_timeline(news_source) 