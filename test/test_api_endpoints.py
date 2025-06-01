#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API端点单元测试
测试所有新闻相关的API端点
"""

import pytest
import asyncio
import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置测试环境变量
os.environ["DATABASE_TYPE"] = "sqlite"
os.environ["DATABASE_PATH"] = ":memory:"
os.environ["AUTH_ENABLED"] = "false"

from api.api import app
from core.models.news_source import NewsSource, NewsSourceStatus, NewsSourceType
from core.models.news_article import NewsArticle, ArticleStatus
from core.service.news_source_repository import NewsSourceRepository
from core.service.news_article_repository import NewsArticleRepository
from datetime import datetime, timedelta

class TestNewsSourcesAPI:
    """测试新闻源相关API"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_news_sources(self):
        """模拟新闻源数据"""
        return [
            NewsSource(
                id=1,
                name="测试新闻源1",
                url="https://example.com/rss1.xml",
                source_type=NewsSourceType.RSS,
                status=NewsSourceStatus.ACTIVE,
                description="测试用的RSS新闻源",
                last_fetch_time=datetime.now(),
                total_articles_fetched=100,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            NewsSource(
                id=2,
                name="测试新闻源2",
                url="https://example.com/api",
                source_type=NewsSourceType.API,
                status=NewsSourceStatus.INACTIVE,
                description="测试用的API新闻源",
                last_fetch_time=None,
                total_articles_fetched=0,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
    
    def test_get_news_sources_success(self, client, mock_news_sources):
        """测试获取新闻源列表 - 成功情况"""
        with patch.object(NewsSourceRepository, 'get_all_news_sources', 
                         new_callable=AsyncMock, return_value=mock_news_sources):
            response = client.get("/news/sources")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["data"]) == 2
            
            # 检查第一个新闻源的数据结构
            source1 = data["data"][0]
            assert source1["id"] == 1
            assert source1["name"] == "测试新闻源1"
            assert source1["url"] == "https://example.com/rss1.xml"
            assert source1["source_type"] == "rss"
            assert source1["status"] == "active"
            assert source1["total_articles"] == 100
    
    def test_get_news_sources_empty(self, client):
        """测试获取新闻源列表 - 空列表"""
        with patch.object(NewsSourceRepository, 'get_all_news_sources', 
                         new_callable=AsyncMock, return_value=[]):
            response = client.get("/news/sources")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"] == []
    
    def test_get_news_sources_error(self, client):
        """测试获取新闻源列表 - 异常情况"""
        with patch.object(NewsSourceRepository, 'get_all_news_sources', 
                         side_effect=Exception("数据库连接失败")):
            response = client.get("/news/sources")
            
            assert response.status_code == 500
            assert "数据库连接失败" in response.json()["detail"]


class TestNewsArticlesAPI:
    """测试新闻文章相关API"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_news_articles(self):
        """模拟新闻文章数据"""
        return [
            NewsArticle(
                id=1,
                title="测试新闻标题1",
                url="https://example.com/news1",
                url_hash="hash1",
                content="这是测试新闻内容1" * 50,  # 长内容用于测试截断
                author="作者1",
                source_id=1,
                status=ArticleStatus.PROCESSED,
                importance_score=0.8,
                market_relevance_score=0.7,
                category="财经",
                sentiment_score=0.5,
                published_at=datetime.now(),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                word_count=500,
                read_time_minutes=3
            ),
            NewsArticle(
                id=2,
                title="测试新闻标题2",
                url="https://example.com/news2",
                url_hash="hash2",
                content="这是测试新闻内容2",
                author="作者2",
                source_id=2,
                status=ArticleStatus.PENDING,
                importance_score=0.6,
                market_relevance_score=0.5,
                category="科技",
                sentiment_score=-0.2,
                published_at=datetime.now() - timedelta(hours=2),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                word_count=300,
                read_time_minutes=2
            )
        ]
    
    def test_get_news_articles_success(self, client, mock_news_articles):
        """测试获取新闻文章列表 - 成功情况"""
        with patch.object(NewsArticleRepository, 'query_articles', 
                         new_callable=AsyncMock, return_value=(mock_news_articles, 2)):
            response = client.get("/news?page=1&page_size=20")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["data"]["articles"]) == 2
            assert data["data"]["pagination"]["total"] == 2
            assert data["data"]["pagination"]["page"] == 1
            assert data["data"]["pagination"]["page_size"] == 20
            
            # 检查文章内容是否被正确截断
            article1 = data["data"]["articles"][0]
            assert len(article1["content"]) <= 203  # 200字符 + "..."
    
    def test_get_news_articles_with_filters(self, client, mock_news_articles):
        """测试获取新闻文章列表 - 带筛选参数"""
        filtered_articles = [mock_news_articles[0]]  # 只返回一篇文章
        
        with patch.object(NewsArticleRepository, 'query_articles', 
                         new_callable=AsyncMock, return_value=(filtered_articles, 1)):
            response = client.get("/news?search=测试&source_id=1&hours=24&status=processed")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert len(data["data"]["articles"]) == 1
            assert data["data"]["pagination"]["total"] == 1
    
    def test_get_news_articles_pagination(self, client, mock_news_articles):
        """测试新闻文章列表分页"""
        with patch.object(NewsArticleRepository, 'query_articles', 
                         new_callable=AsyncMock, return_value=(mock_news_articles, 20)):
            response = client.get("/news?page=2&page_size=5")
            
            assert response.status_code == 200
            data = response.json()
            pagination = data["data"]["pagination"]
            assert pagination["page"] == 2
            assert pagination["page_size"] == 5
            assert pagination["total"] == 20
            assert pagination["total_pages"] == 4
            assert pagination["has_next"] == True
            assert pagination["has_prev"] == True
    
    def test_get_news_article_by_id_success(self, client, mock_news_articles):
        """测试获取单篇新闻文章 - 成功情况"""
        article = mock_news_articles[0]
        
        with patch.object(NewsArticleRepository, 'get_article_by_id', 
                         new_callable=AsyncMock, return_value=article):
            response = client.get("/news/1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            article_data = data["data"]
            assert article_data["id"] == 1
            assert article_data["title"] == "测试新闻标题1"
            assert article_data["word_count"] == 500
            assert article_data["read_time_minutes"] == 3
    
    def test_get_news_article_by_id_not_found(self, client):
        """测试获取单篇新闻文章 - 文章不存在"""
        with patch.object(NewsArticleRepository, 'get_article_by_id', 
                         new_callable=AsyncMock, return_value=None):
            response = client.get("/news/999")
            
            assert response.status_code == 404
            assert "文章不存在" in response.json()["detail"]
    
    def test_get_news_articles_error(self, client):
        """测试获取新闻文章列表 - 异常情况"""
        with patch.object(NewsArticleRepository, 'query_articles', 
                         side_effect=Exception("查询失败")):
            response = client.get("/news")
            
            assert response.status_code == 500
            assert "查询失败" in response.json()["detail"]


class TestNewsStatusAPI:
    """测试新闻状态API"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_aggregation_stats(self):
        """模拟聚合统计数据"""
        return {
            'source_stats': {
                'total': 15,
                'active': 11,
                'error': 0,
                'suspended': 0,
                'inactive': 4
            },
            'article_stats': {
                'total': 150,
                'pending': 10,
                'processed': 130,
                'failed': 5,
                'archived': 5,
                'today_count': 25
            },
            'recent_fetches': [
                {
                    'name': '测试RSS源',
                    'last_fetch_time': '2025-05-31T17:13:27',
                    'total_articles': 100,
                    'status': 'active'
                }
            ],
            'total_sources': 15,
            'total_articles': 150
        }
    
    def test_get_news_fetch_status_success(self, client, mock_aggregation_stats):
        """测试获取新闻抓取状态 - 成功情况"""
        from core.news_aggregator.news_aggregator_manager import NewsAggregatorManager
        
        with patch.object(NewsAggregatorManager, 'get_aggregation_stats', 
                         new_callable=AsyncMock, return_value=mock_aggregation_stats):
            response = client.get("/cron/news/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            
            stats = data["data"]
            assert stats["source_stats"]["total"] == 15
            assert stats["article_stats"]["total"] == 150
            assert stats["article_stats"]["today_count"] == 25
            assert len(stats["recent_fetches"]) == 1
    
    def test_get_news_fetch_status_error(self, client):
        """测试获取新闻抓取状态 - 异常情况"""
        from core.news_aggregator.news_aggregator_manager import NewsAggregatorManager
        
        with patch.object(NewsAggregatorManager, 'get_aggregation_stats', 
                         side_effect=Exception("统计失败")):
            response = client.get("/cron/news/status")
            
            assert response.status_code == 500
            assert "统计失败" in response.json()["detail"]


class TestNewsCronAPI:
    """测试新闻定时任务API"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)
    
    def test_cron_fetch_news_success(self, client):
        """测试定时新闻抓取任务 - 成功情况"""
        response = client.post("/cron/news", json={"source_ids": [1, 2], "limit": 50})
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "新闻抓取任务已启动" in data["message"]
        assert data["task_info"]["source_ids"] == [1, 2]
        assert data["task_info"]["limit"] == 50
    
    def test_cron_fetch_news_default_params(self, client):
        """测试定时新闻抓取任务 - 默认参数"""
        response = client.post("/cron/news", json={})
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["task_info"]["source_ids"] == "all_active"
        assert data["task_info"]["limit"] == 50
    
    def test_cron_fetch_news_no_body(self, client):
        """测试定时新闻抓取任务 - 无请求体"""
        response = client.post("/cron/news")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


# 运行测试的主函数
if __name__ == "__main__":
    # 设置测试环境
    os.environ["DATABASE_TYPE"] = "sqlite"
    os.environ["DATABASE_PATH"] = ":memory:"
    os.environ["AUTH_ENABLED"] = "false"
    
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"]) 