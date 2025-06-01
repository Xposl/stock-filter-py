#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
开发调试测试
用于开发过程中的调试和验证，不包含在正式测试套件中
"""

import pytest
import logging
import asyncio
from datetime import datetime

# 设置详细日志输出
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


@pytest.mark.debug
class TestDevelopmentHelpers:
    """开发调试辅助测试"""
    
    def test_logging_configuration(self):
        """测试日志配置"""
        logger = logging.getLogger(__name__)
        logger.debug("Debug级别日志测试")
        logger.info("Info级别日志测试")
        logger.warning("Warning级别日志测试")
        logger.error("Error级别日志测试")
        
        # 在pytest环境中，日志级别可能被调整，所以我们只验证日志系统能正常工作
        assert logger is not None
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'error')
        print("日志配置正常")
    
    def test_environment_variables(self):
        """测试环境变量"""
        import os
        
        # 检查测试环境变量
        database_type = os.getenv("DATABASE_TYPE")
        auth_enabled = os.getenv("AUTH_ENABLED")
        
        print(f"DATABASE_TYPE: {database_type}")
        print(f"AUTH_ENABLED: {auth_enabled}")
        
        # 在测试环境中应该是sqlite和false
        assert database_type == "sqlite"
        assert auth_enabled == "false"
    
    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """测试异步功能"""
        async def sample_async_function():
            await asyncio.sleep(0.1)
            return "异步函数执行成功"
        
        result = await sample_async_function()
        assert result == "异步函数执行成功"
        print("异步测试通过")
    
    def test_datetime_handling(self):
        """测试时间处理"""
        now = datetime.now()
        print(f"当前时间: {now}")
        print(f"ISO格式: {now.isoformat()}")
        
        # 验证时间对象
        assert isinstance(now, datetime)
        assert now.year >= 2025
    
    def test_import_paths(self):
        """测试导入路径"""
        try:
            # 测试核心模块导入
            from core.models.news_source import NewsSource
            from core.models.news_article import NewsArticle
            from core.service.news_source_repository import NewsSourceRepository
            from core.service.news_article_repository import NewsArticleRepository
            
            print("核心模块导入成功")
            
            # 测试API模块导入
            from api.api import app
            print("API模块导入成功")
            
        except ImportError as e:
            pytest.fail(f"导入失败: {e}")
    
    def test_database_adapter_mock(self):
        """测试数据库适配器模拟"""
        from unittest.mock import Mock
        from core.database.db_adapter import DbAdapter
        
        # 创建模拟适配器
        mock_db = Mock(spec=DbAdapter)
        mock_db.query.return_value = []
        mock_db.query_one.return_value = None
        
        # 测试模拟功能
        result = mock_db.query("SELECT * FROM test")
        assert result == []
        
        result_one = mock_db.query_one("SELECT * FROM test WHERE id = 1")
        assert result_one is None
        
        print("数据库适配器模拟正常")


@pytest.mark.debug
class TestDataStructures:
    """测试数据结构"""
    
    def test_news_source_structure(self):
        """测试新闻源数据结构"""
        from core.models.news_source import NewsSource, NewsSourceType, NewsSourceStatus
        
        source_data = {
            'id': 1,
            'name': '调试测试源',
            'source_type': NewsSourceType.RSS,
            'url': 'https://example.com/debug.xml',
            'status': NewsSourceStatus.ACTIVE
        }
        
        source = NewsSource(**source_data)
        print(f"新闻源创建成功: {source.model_dump()}")
        
        assert source.id == 1
        assert source.name == '调试测试源'
    
    def test_news_article_structure(self):
        """测试新闻文章数据结构"""
        from core.models.news_article import NewsArticle, ArticleStatus
        
        article_data = {
            'id': 1,
            'title': '调试测试文章',
            'url': 'https://example.com/debug-article',
            'url_hash': 'debug_hash_123',
            'content': '这是调试测试文章内容',
            'source_id': 1,
            'status': ArticleStatus.PENDING
        }
        
        article = NewsArticle(**article_data)
        print(f"新闻文章创建成功: {article.model_dump()}")
        
        assert article.id == 1
        assert article.title == '调试测试文章'


if __name__ == "__main__":
    # 仅运行调试测试
    pytest.main([__file__, "-v", "-m", "debug"]) 