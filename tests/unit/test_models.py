#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据模型单元测试
测试Pydantic模型的验证和序列化功能
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from core.models.news_source import NewsSource, NewsSourceType, NewsSourceStatus, NewsSourceCreate
from core.models.news_article import NewsArticle, ArticleStatus, NewsArticleCreate


@pytest.mark.unit
class TestNewsSourceModel:
    """测试NewsSource模型"""
    
    def test_news_source_creation_valid(self):
        """测试有效的新闻源创建"""
        # Arrange
        source_data = {
            'id': 1,
            'name': '测试新闻源',
            'description': '这是一个测试新闻源',
            'source_type': NewsSourceType.RSS,
            'url': 'https://example.com/rss.xml',
            'status': NewsSourceStatus.ACTIVE,
            'max_articles_per_fetch': 50,
            'language': 'zh',
            'region': 'CN',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        # Act
        source = NewsSource(**source_data)
        
        # Assert
        assert source.id == 1
        assert source.name == '测试新闻源'
        assert source.source_type == NewsSourceType.RSS
        assert source.status == NewsSourceStatus.ACTIVE
        assert source.url == 'https://example.com/rss.xml'
    
    def test_news_source_enum_validation(self):
        """测试枚举字段验证"""
        # 测试有效的source_type
        source = NewsSource(
            id=1,
            name='测试源',
            source_type='rss',  # 字符串会被转换为枚举
            url='https://example.com/rss',
            status='active'
        )
        assert source.source_type == NewsSourceType.RSS
        assert source.status == NewsSourceStatus.ACTIVE
    
    def test_news_source_required_fields(self):
        """测试必需字段"""
        # 测试缺少必需字段
        with pytest.raises(ValidationError):
            NewsSource(
                id=1,
                name='测试源'
                # 缺少source_type和url
            )
    
    def test_news_source_create_model(self):
        """测试NewsSourceCreate模型"""
        # Arrange
        create_data = {
            'name': '新建新闻源',
            'description': '新建的测试源',
            'source_type': 'rss',
            'url': 'https://newexample.com/feed.xml',
            'max_articles_per_fetch': 30
        }
        
        # Act
        source_create = NewsSourceCreate(**create_data)
        
        # Assert
        assert source_create.name == '新建新闻源'
        assert source_create.source_type == NewsSourceType.RSS
        assert source_create.max_articles_per_fetch == 30


@pytest.mark.unit
class TestNewsArticleModel:
    """测试NewsArticle模型"""
    
    def test_news_article_creation_valid(self):
        """测试有效的新闻文章创建"""
        # Arrange
        article_data = {
            'id': 1,
            'title': '测试新闻标题',
            'url': 'https://example.com/news/1',
            'url_hash': 'abc123hash',
            'content': '这是新闻内容',
            'author': '测试作者',
            'source_id': 1,
            'category': '财经',
            'status': ArticleStatus.PROCESSED,
            'published_at': datetime.now(),
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'word_count': 100,
            'read_time_minutes': 2
        }
        
        # Act
        article = NewsArticle(**article_data)
        
        # Assert
        assert article.id == 1
        assert article.title == '测试新闻标题'
        assert article.status == ArticleStatus.PROCESSED
        assert article.word_count == 100
        assert article.read_time_minutes == 2
    
    def test_news_article_score_fields(self):
        """测试评分字段"""
        # 测试有效评分
        article = NewsArticle(
            id=1,
            title='评分测试',
            url='https://example.com/test',
            url_hash='hash123',
            content='测试内容',
            source_id=1,
            importance_score=0.8,
            market_relevance_score=0.7,
            sentiment_score=0.1
        )
        
        assert article.importance_score == 0.8
        assert article.market_relevance_score == 0.7
        assert article.sentiment_score == 0.1
        
        # 测试默认值
        article_default = NewsArticle(
            id=2,
            title='默认评分测试',
            url='https://example.com/default',
            url_hash='hash456',
            content='测试内容',
            source_id=1
        )
        
        assert article_default.importance_score == 0.0
        assert article_default.market_relevance_score == 0.0
        assert article_default.sentiment_score is None
    
    def test_news_article_status_enum(self):
        """测试文章状态枚举"""
        # 测试所有有效状态
        valid_statuses = ['pending', 'processed', 'failed', 'archived']
        
        for status_str in valid_statuses:
            article = NewsArticle(
                id=1,
                title=f'状态测试-{status_str}',
                url=f'https://example.com/{status_str}',
                url_hash=f'hash_{status_str}',
                content='状态测试内容',
                source_id=1,
                status=status_str
            )
            
            # 验证字符串被正确转换为枚举
            assert isinstance(article.status, ArticleStatus)
    
    def test_news_article_create_model(self):
        """测试NewsArticleCreate模型"""
        # Arrange
        create_data = {
            'title': '新建文章',
            'url': 'https://example.com/new-article',
            'content': '新建文章内容',
            'author': '新建作者',
            'source_id': 1,
            'category': '科技',
            'published_at': datetime.now()
        }
        
        # Act
        article_create = NewsArticleCreate(**create_data)
        
        # Assert
        assert article_create.title == '新建文章'
        assert article_create.source_id == 1
        assert article_create.category == '科技'
    
    def test_news_article_optional_fields(self):
        """测试可选字段"""
        # 测试最小必需字段
        article = NewsArticle(
            id=1,
            title='最小字段测试',
            url='https://example.com/minimal',
            url_hash='minimal_hash',
            content='最小内容',
            source_id=1
        )
        
        # 验证可选字段为None或默认值
        assert article.author is None
        assert article.category is None
        assert article.summary is None
        assert article.entities is None
        assert article.keywords is None
        assert article.topics is None
    
    def test_news_article_required_fields(self):
        """测试必需字段"""
        # 测试缺少必需字段
        with pytest.raises(ValidationError):
            NewsArticle(
                id=1,
                title='缺少字段测试'
                # 缺少url, url_hash, source_id
            )


@pytest.mark.unit
class TestModelSerialization:
    """测试模型序列化"""
    
    def test_news_source_json_serialization(self):
        """测试新闻源JSON序列化"""
        # Arrange
        source = NewsSource(
            id=1,
            name='序列化测试源',
            source_type=NewsSourceType.RSS,
            url='https://example.com/serialize',
            status=NewsSourceStatus.ACTIVE
        )
        
        # Act
        json_data = source.model_dump()
        
        # Assert
        assert isinstance(json_data, dict)
        assert json_data['id'] == 1
        assert json_data['name'] == '序列化测试源'
        assert json_data['source_type'] == 'rss'
        assert json_data['status'] == 'active'
    
    def test_news_article_json_serialization(self):
        """测试新闻文章JSON序列化"""
        # Arrange
        article = NewsArticle(
            id=1,
            title='序列化测试文章',
            url='https://example.com/serialize-article',
            url_hash='serialize_hash',
            content='序列化测试内容',
            source_id=1,
            status=ArticleStatus.PROCESSED,
            importance_score=0.9
        )
        
        # Act
        json_data = article.model_dump()
        
        # Assert
        assert isinstance(json_data, dict)
        assert json_data['id'] == 1
        assert json_data['title'] == '序列化测试文章'
        assert json_data['status'] == 'processed'
        assert json_data['importance_score'] == 0.9
    
    def test_model_exclude_none(self):
        """测试排除None值的序列化"""
        # Arrange
        article = NewsArticle(
            id=1,
            title='排除None测试',
            url='https://example.com/exclude-none',
            url_hash='exclude_hash',
            content='测试内容',
            source_id=1,
            author=None,  # 显式设置为None
            category=None
        )
        
        # Act
        json_data = article.model_dump(exclude_none=True)
        
        # Assert
        assert 'author' not in json_data
        assert 'category' not in json_data
        assert 'title' in json_data
        assert 'content' in json_data 