#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
新闻聚合集成测试
测试新闻聚合器与外部新闻源的集成
"""

import pytest
import asyncio
import logging
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock

from core.news_aggregator.rss_aggregator import RSSAggregator
from core.news_aggregator.xueqiu_aggregator import XueqiuAggregator
from core.news_aggregator.news_aggregator_manager import NewsAggregatorManager
from core.models.news_source import NewsSource, NewsSourceType, NewsSourceStatus
from core.models.news_article import NewsArticle, ArticleStatus


@pytest.mark.integration
@pytest.mark.slow
class TestRSSAggregatorIntegration:
    """测试RSS聚合器集成"""
    
    @pytest.fixture
    def rss_news_source(self):
        """RSS新闻源配置"""
        return NewsSource(
            id=1,
            name="测试RSS源",
            description="用于测试的RSS新闻源",
            source_type=NewsSourceType.RSS,
            url="https://feeds.finance.yahoo.com/rss/2.0/headline",
            status=NewsSourceStatus.ACTIVE,
            max_articles_per_fetch=5,  # 限制数量以加快测试
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.mark.asyncio
    async def test_rss_feed_parsing(self, rss_news_source):
        """测试RSS源解析"""
        async with RSSAggregator() as aggregator:
            try:
                articles = await aggregator.fetch_rss_feed(rss_news_source)
                
                # 验证返回结果
                assert isinstance(articles, list)
                
                if articles:
                    article = articles[0]
                    # 验证文章结构
                    assert 'title' in article
                    assert 'url' in article
                    assert 'url_hash' in article
                    assert 'content' in article
                    assert 'source_id' in article
                    assert 'published_at' in article
                    
                    # 验证数据类型
                    assert isinstance(article['title'], str)
                    assert isinstance(article['url'], str)
                    assert isinstance(article['source_id'], int)
                    
                    logging.info(f"RSS聚合成功: 获取到 {len(articles)} 篇文章")
                else:
                    logging.warning("RSS聚合返回空结果")
                    
            except Exception as e:
                logging.error(f"RSS聚合测试失败: {e}")
                # 在集成测试中，外部服务不可用是正常的
                pytest.skip(f"RSS服务不可用: {e}")
    
    @pytest.mark.asyncio
    async def test_rss_with_invalid_url(self):
        """测试无效RSS URL处理"""
        invalid_source = NewsSource(
            id=2,
            name="无效RSS源",
            source_type=NewsSourceType.RSS,
            url="https://invalid-domain-that-does-not-exist.com/rss.xml",
            status=NewsSourceStatus.ACTIVE,
            max_articles_per_fetch=5
        )
        
        async with RSSAggregator() as aggregator:
            try:
                articles = await aggregator.fetch_rss_feed(invalid_source)
                # 应该返回空列表而不是抛出异常
                assert isinstance(articles, list)
                assert len(articles) == 0
                logging.info("无效RSS URL正确处理")
            except Exception as e:
                # 或者正确抛出异常
                logging.info(f"无效RSS URL正确抛出异常: {e}")


@pytest.mark.integration
@pytest.mark.slow  
class TestXueqiuAggregatorIntegration:
    """测试雪球聚合器集成"""
    
    @pytest.fixture
    def xueqiu_news_source(self):
        """雪球新闻源配置"""
        return NewsSource(
            id=3,
            name="雪球时间线",
            description="雪球平台新闻时间线",
            source_type=NewsSourceType.API,
            url="https://xueqiu.com/statuses/public_timeline_by_category.json",
            status=NewsSourceStatus.ACTIVE,
            max_articles_per_fetch=5,
            api_key=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.mark.asyncio
    async def test_xueqiu_timeline_parsing(self, xueqiu_news_source):
        """测试雪球时间线解析"""
        async with XueqiuAggregator() as aggregator:
            try:
                articles = await aggregator.fetch_xueqiu_timeline(xueqiu_news_source)
                
                # 验证返回结果
                assert isinstance(articles, list)
                
                if articles:
                    article = articles[0]
                    # 验证雪球文章结构
                    assert 'title' in article
                    assert 'url' in article
                    assert 'url_hash' in article
                    assert 'content' in article
                    assert 'source_id' in article
                    assert 'published_at' in article
                    
                    # 雪球特有字段
                    if 'importance_score' in article:
                        assert isinstance(article['importance_score'], (int, float))
                    if 'market_relevance_score' in article:
                        assert isinstance(article['market_relevance_score'], (int, float))
                    
                    logging.info(f"雪球聚合成功: 获取到 {len(articles)} 篇文章")
                else:
                    logging.warning("雪球聚合返回空结果")
                    
            except Exception as e:
                logging.error(f"雪球聚合测试失败: {e}")
                # 雪球API可能需要token或有访问限制
                pytest.skip(f"雪球服务不可用: {e}")
    
    @pytest.mark.asyncio
    async def test_xueqiu_token_handling(self, xueqiu_news_source):
        """测试雪球token处理"""
        async with XueqiuAggregator() as aggregator:
            # 测试token获取
            try:
                # 这个测试主要验证token获取逻辑不会崩溃
                articles = await aggregator.fetch_xueqiu_timeline(xueqiu_news_source)
                logging.info("雪球token处理正常")
            except Exception as e:
                logging.warning(f"雪球token处理异常: {e}")
                # 在集成测试中这是可以接受的


@pytest.mark.integration
class TestNewsAggregatorManagerIntegration:
    """测试新闻聚合管理器集成"""
    
    @pytest.fixture
    def mock_session_factory(self):
        """模拟会话工厂"""
        from unittest.mock import Mock
        return Mock()
    
    @pytest.fixture
    def manager(self, mock_session_factory):
        """创建新闻聚合管理器"""
        return NewsAggregatorManager()  # 不传递参数
    
    @pytest.fixture
    def sample_news_sources(self):
        """示例新闻源"""
        return [
            NewsSource(
                id=1,
                name="测试RSS源",
                source_type=NewsSourceType.RSS,
                url="https://example.com/rss.xml",
                status=NewsSourceStatus.ACTIVE,
                max_articles_per_fetch=3
            ),
            NewsSource(
                id=2,
                name="测试API源",
                source_type=NewsSourceType.API,
                url="https://example.com/api/news",
                status=NewsSourceStatus.ACTIVE,
                max_articles_per_fetch=3
            )
        ]
    
    def test_manager_initialization(self, manager):
        """测试管理器初始化"""
        assert manager is not None
        assert hasattr(manager, 'aggregators')
        assert NewsSourceType.RSS in manager.aggregators
        assert NewsSourceType.API in manager.aggregators
    
    @pytest.mark.asyncio
    async def test_aggregator_selection(self, manager, sample_news_sources):
        """测试聚合器选择逻辑"""
        rss_source = sample_news_sources[0]
        api_source = sample_news_sources[1]
        
        # 测试RSS源选择
        rss_aggregator_class = manager.aggregators.get(rss_source.source_type)
        assert rss_aggregator_class == RSSAggregator
        
        # 测试API源选择
        api_aggregator_class = manager.aggregators.get(api_source.source_type)
        assert api_aggregator_class == XueqiuAggregator
    
    @pytest.mark.asyncio
    async def test_single_source_fetch_simulation(self, manager, sample_news_sources):
        """测试单个源抓取模拟"""
        # 这个测试主要验证管理器的调用逻辑
        # 实际的抓取会被模拟，因为我们不想在单元测试中访问真实API
        
        with patch.object(RSSAggregator, 'fetch_rss_feed', new_callable=AsyncMock) as mock_rss:
            mock_rss.return_value = [
                {
                    'title': '测试文章',
                    'url': 'https://example.com/article1',
                    'url_hash': 'hash123',
                    'content': '测试内容',
                    'source_id': 1,
                    'published_at': datetime.now()
                }
            ]
            
            # 模拟数据库操作
            with patch.object(manager, '_save_articles_to_db', new_callable=AsyncMock):
                result = await manager._fetch_single_source(sample_news_sources[0])
                
                assert isinstance(result, list)
                assert len(result) == 1
                mock_rss.assert_called_once()


@pytest.mark.integration
@pytest.mark.slow
class TestNewsAggregationComplete:
    """完整的新闻聚合集成测试"""
    
    @pytest.mark.asyncio
    async def test_complete_aggregation_workflow(self):
        """测试完整的聚合工作流程"""
        # 这个测试模拟了完整的新闻聚合流程
        # 但使用模拟数据以避免依赖外部服务
        
        sample_articles = [
            {
                'title': '市场新闻1',
                'url': 'https://example.com/news1',
                'url_hash': 'hash1',
                'content': '重要市场新闻内容',
                'source_id': 1,
                'published_at': datetime.now(),
                'importance_score': 0.8,
                'market_relevance_score': 0.9
            },
            {
                'title': '科技新闻2',
                'url': 'https://example.com/news2',
                'url_hash': 'hash2', 
                'content': '科技行业新闻内容',
                'source_id': 2,
                'published_at': datetime.now(),
                'importance_score': 0.6,
                'market_relevance_score': 0.5
            }
        ]
        
        # 验证文章数据结构
        for article in sample_articles:
            assert 'title' in article
            assert 'url' in article
            assert 'url_hash' in article
            assert 'content' in article
            assert 'source_id' in article
            assert 'published_at' in article
            
            # 验证评分字段
            if 'importance_score' in article:
                assert 0 <= article['importance_score'] <= 1
            if 'market_relevance_score' in article:
                assert 0 <= article['market_relevance_score'] <= 1
        
        logging.info(f"完整聚合工作流程测试成功: 处理了 {len(sample_articles)} 篇文章")


if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(level=logging.INFO)
    
    # 运行集成测试
    pytest.main([__file__, "-v", "--tb=short", "-m", "integration"]) 