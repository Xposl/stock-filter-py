#!/usr/bin/env python3

"""
Repository层单元测试
测试NewsSourceRepository和NewsArticleRepository的数据访问功能
"""

from datetime import datetime

import pytest

from core.models.news_article import ArticleStatus, NewsArticle
from core.models.news_source import NewsSource, NewsSourceStatus, NewsSourceType
from core.service.news_article_repository import NewsArticleRepository
from core.service.news_source_repository import NewsSourceRepository


@pytest.mark.unit
class TestNewsSourceRepository:
    """测试NewsSourceRepository"""

    @pytest.fixture
    def repository(self, mock_db_adapter):
        """创建Repository实例"""
        repo = NewsSourceRepository()
        repo.db = mock_db_adapter
        return repo

    @pytest.fixture
    def mock_source_data(self):
        """模拟数据库返回的新闻源数据"""
        return {
            'id': 1,
            'name': '测试新闻源',
            'description': '测试描述',
            'source_type': 'rss',
            'url': 'https://example.com/rss.xml',
            'api_key': None,
            'update_frequency': 3600,
            'max_articles_per_fetch': 50,
            'filter_keywords': None,
            'filter_categories': None,
            'language': 'zh',
            'region': 'CN',
            'status': 'active',
            'last_fetch_time': datetime.now(),
            'last_error_message': None,
            'total_articles_fetched': 100,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }

    @pytest.mark.asyncio
    async def test_get_news_source_by_id_success(self, repository, mock_source_data):
        """测试根据ID获取新闻源 - 成功情况"""
        # Arrange
        repository.db.query_one.return_value = mock_source_data

        # Act
        result = await repository.get_news_source_by_id(1)

        # Assert
        assert result is not None
        assert isinstance(result, NewsSource)
        assert result.id == 1
        assert result.name == '测试新闻源'
        assert result.source_type == NewsSourceType.RSS
        assert result.status == NewsSourceStatus.ACTIVE

        repository.db.query_one.assert_called_once_with(
            "SELECT * FROM news_sources WHERE id = :id",
            {"id": 1}
        )

    @pytest.mark.asyncio
    async def test_get_news_source_by_id_not_found(self, repository):
        """测试根据ID获取新闻源 - 未找到"""
        # Arrange
        repository.db.query_one.return_value = None

        # Act
        result = await repository.get_news_source_by_id(999)

        # Assert
        assert result is None
        repository.db.query_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_news_sources_success(self, repository, mock_source_data):
        """测试获取所有新闻源 - 成功情况"""
        # Arrange
        repository.db.query.return_value = [mock_source_data, mock_source_data]

        # Act
        result = await repository.get_all_news_sources(limit=100, offset=0)

        # Assert
        assert len(result) == 2
        assert all(isinstance(source, NewsSource) for source in result)

        repository.db.query.assert_called_once_with(
            "SELECT * FROM news_sources ORDER BY created_at DESC LIMIT :limit OFFSET :offset",
            {"limit": 100, "offset": 0}
        )

    @pytest.mark.asyncio
    async def test_get_all_news_sources_empty(self, repository):
        """测试获取所有新闻源 - 空结果"""
        # Arrange
        repository.db.query.return_value = []

        # Act
        result = await repository.get_all_news_sources()

        # Assert
        assert result == []
        repository.db.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_news_source_stats_success(self, repository):
        """测试获取新闻源统计信息 - 成功情况"""
        # Arrange
        status_results = [
            {'status': 'active', 'count': 10},
            {'status': 'inactive', 'count': 3},
            {'status': 'error', 'count': 1}
        ]

        type_results = [
            {'source_type': 'rss', 'count': 12},
            {'source_type': 'api', 'count': 2}
        ]

        total_result = {'total': 1500}

        repository.db.query.side_effect = [status_results, type_results]
        repository.db.query_one.return_value = total_result

        # Act
        result = await repository.get_news_source_stats()

        # Assert
        assert result['by_status']['active'] == 10
        assert result['by_status']['inactive'] == 3
        assert result['by_status']['error'] == 1
        assert result['by_type']['rss'] == 12
        assert result['by_type']['api'] == 2
        assert result['total_articles_fetched'] == 1500

        # 验证调用了正确的SQL
        assert repository.db.query.call_count == 2
        repository.db.query_one.assert_called_once()


@pytest.mark.unit
class TestNewsArticleRepository:
    """测试NewsArticleRepository"""

    @pytest.fixture
    def repository(self, mock_db_adapter):
        """创建Repository实例"""
        repo = NewsArticleRepository()
        repo.db = mock_db_adapter
        return repo

    @pytest.fixture
    def mock_article_data(self):
        """模拟数据库返回的新闻文章数据"""
        return {
            'id': 1,
            'title': '测试新闻标题',
            'url': 'https://example.com/news/1',
            'url_hash': 'abc123',
            'content': '这是测试新闻内容',
            'summary': '测试摘要',
            'author': '测试作者',
            'source_id': 1,
            'source_name': '测试新闻源',
            'category': '财经',
            'published_at': datetime.now(),
            'crawled_at': datetime.now(),
            'language': 'zh',
            'region': 'CN',
            'entities': None,
            'keywords': None,
            'sentiment_score': 0.5,
            'topics': None,
            'importance_score': 0.8,
            'market_relevance_score': 0.7,
            'status': 'processed',
            'processed_at': datetime.now(),
            'error_message': None,
            'word_count': 100,
            'read_time_minutes': 2,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }

    @pytest.mark.asyncio
    async def test_get_article_by_id_success(self, repository, mock_article_data):
        """测试根据ID获取新闻文章 - 成功情况"""
        # Arrange
        repository.db.query_one.return_value = mock_article_data

        # Act
        result = await repository.get_article_by_id(1)

        # Assert
        assert result is not None
        assert isinstance(result, NewsArticle)
        assert result.id == 1
        assert result.title == '测试新闻标题'
        assert result.status == ArticleStatus.PROCESSED

        repository.db.query_one.assert_called_once_with(
            "SELECT * FROM news_articles WHERE id = :id",
            {"id": 1}
        )

    @pytest.mark.asyncio
    async def test_get_article_by_id_not_found(self, repository):
        """测试根据ID获取新闻文章 - 未找到"""
        # Arrange
        repository.db.query_one.return_value = None

        # Act
        result = await repository.get_article_by_id(999)

        # Assert
        assert result is None
        repository.db.query_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_articles_success(self, repository, mock_article_data):
        """测试综合查询新闻文章 - 成功情况"""
        # Arrange
        repository.db.query_one.return_value = {'total': 5}
        repository.db.query.return_value = [mock_article_data, mock_article_data]

        # Act
        articles, total = await repository.query_articles(
            page=1,
            page_size=20,
            search="测试",
            source_id=1,
            hours=24,
            status="processed"
        )

        # Assert
        assert len(articles) == 2
        assert total == 5
        assert all(isinstance(article, NewsArticle) for article in articles)

        # 验证调用了正确的方法
        repository.db.query_one.assert_called_once()  # 总数查询
        repository.db.query.assert_called_once()      # 数据查询

    @pytest.mark.asyncio
    async def test_query_articles_with_filters(self, repository, mock_article_data):
        """测试带筛选条件的查询"""
        # Arrange
        repository.db.query_one.return_value = {'total': 1}
        repository.db.query.return_value = [mock_article_data]

        # Act
        articles, total = await repository.query_articles(
            page=1,
            page_size=10,
            search="财经",
            source_id=1,
            hours=12,
            status="processed"
        )

        # Assert
        assert len(articles) == 1
        assert total == 1

        # 验证调用了查询方法
        repository.db.query_one.assert_called_once()
        repository.db.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_articles_empty_result(self, repository):
        """测试查询新闻文章 - 空结果"""
        # Arrange
        repository.db.query_one.return_value = {'total': 0}
        repository.db.query.return_value = []

        # Act
        articles, total = await repository.query_articles(page=1, page_size=20)

        # Assert
        assert articles == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_get_recent_articles_success(self, repository, mock_article_data):
        """测试获取最近新闻文章 - 成功情况"""
        # Arrange
        repository.db.query.return_value = [mock_article_data]

        # Act
        result = await repository.get_recent_articles(hours=24, limit=50)

        # Assert
        assert len(result) == 1
        assert isinstance(result[0], NewsArticle)

        repository.db.query.assert_called_once()
        # 验证SQL包含时间筛选条件
        call_args = repository.db.query.call_args
        assert "crawled_at >= :cutoff_time" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_search_articles_success(self, repository, mock_article_data):
        """测试搜索新闻文章 - 成功情况"""
        # Arrange
        repository.db.query.return_value = [mock_article_data]

        # Act
        result = await repository.search_articles(query="测试", limit=10, offset=0)

        # Assert
        assert len(result) == 1
        assert isinstance(result[0], NewsArticle)

        repository.db.query.assert_called_once()
        # 验证SQL包含搜索条件
        call_args = repository.db.query.call_args
        assert "LIKE :query" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_get_article_stats_success(self, repository):
        """测试获取文章统计信息 - 成功情况"""
        # Arrange
        status_results = [
            {'status': 'processed', 'count': 100},
            {'status': 'pending', 'count': 20},
            {'status': 'failed', 'count': 5}
        ]

        source_results = [
            {'source_name': '测试源1', 'count': 80},
            {'source_name': '测试源2', 'count': 45}
        ]

        today_result = {'count': 15}
        total_result = {'total': 125}

        repository.db.query.side_effect = [status_results, source_results]
        repository.db.query_one.side_effect = [today_result, total_result]

        # Act
        result = await repository.get_article_stats()

        # Assert
        assert result['by_status']['processed'] == 100
        assert result['by_status']['pending'] == 20
        assert result['by_status']['failed'] == 5
        assert result['by_source']['测试源1'] == 80
        assert result['by_source']['测试源2'] == 45
        assert result['today_count'] == 15
        assert result['total_count'] == 125

        # 验证调用了正确的次数
        assert repository.db.query.call_count == 2
        assert repository.db.query_one.call_count == 2
