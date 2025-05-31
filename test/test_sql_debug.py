#!/usr/bin/env python3

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.database.db_adapter import DbAdapter

def test_sql_conversion():
    db = DbAdapter()
    
    sql = """
    INSERT INTO news_articles (
        title, url, url_hash, content, summary, author, source_id, source_name, category,
        published_at, crawled_at, language, region, entities, keywords, sentiment_score,
        topics, importance_score, market_relevance_score, status, processed_at,
        error_message, word_count, read_time_minutes, created_at, updated_at
    ) VALUES (
        :title, :url, :url_hash, :content, :summary, :author, :source_id, :source_name, :category,
        :published_at, :crawled_at, :language, :region, :entities, :keywords, :sentiment_score,
        :topics, :importance_score, :market_relevance_score, :status, :processed_at,
        :error_message, :word_count, :read_time_minutes, :created_at, :updated_at
    )
    """
    
    params = {
        'title': '测试文章',
        'url': 'https://test.com/article1',
        'url_hash': 'test_hash',
        'content': None,
        'summary': None,
        'author': None,
        'source_id': 15,
        'source_name': '测试源',
        'category': None,
        'published_at': None,
        'crawled_at': '2025-05-31 17:00:00',
        'language': 'zh',
        'region': 'CN',
        'entities': None,
        'keywords': None,
        'sentiment_score': None,
        'topics': None,
        'importance_score': 0.0,
        'market_relevance_score': 0.0,
        'status': 'pending',
        'processed_at': None,
        'error_message': None,
        'word_count': 0,
        'read_time_minutes': 0,
        'created_at': '2025-05-31 17:00:00',
        'updated_at': '2025-05-31 17:00:00'
    }
    
    converted_sql, converted_params = db._convert_sql_params(sql, params)
    
    print("原始SQL:")
    print(sql)
    print("\n转换后SQL:")
    print(converted_sql)
    print("\n参数:")
    print(converted_params)
    print(f"\n数据库类型: {db.db_type}")

if __name__ == "__main__":
    test_sql_conversion() 