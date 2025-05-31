#!/usr/bin/env python3

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.handler.news_article_handler import NewsArticleHandler
from core.models.news_article import NewsArticleCreate, news_article_to_dict

# 配置调试日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test():
    handler = NewsArticleHandler()
    
    # 创建完整的文章数据
    article_create = NewsArticleCreate(
        title='测试文章',
        url='https://test.com/article1',
        source_id=15,
        source_name='测试源'
    )
    
    print("创建的模型:")
    print(article_create)
    
    print("\n转换为字典:")
    article_dict = news_article_to_dict(article_create)
    print(article_dict)
    
    result = await handler.create_news_article(article_dict)
    print(f'\n结果: {result}')

if __name__ == "__main__":
    asyncio.run(test()) 