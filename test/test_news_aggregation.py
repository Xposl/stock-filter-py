#!/usr/bin/env python3
"""
新闻聚合功能测试脚本
测试英为财情等RSS源的数据抓取功能
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core.database.news_db_init import NewsDBInitializer
from core.news_aggregator.rss_aggregator import RSSAggregator
from core.news_aggregator.news_aggregator_manager import NewsAggregatorManager
from core.models.news_source import NewsSource, NewsSourceType, NewsSourceStatus

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_investing_rss_sources():
    """测试英为财情等RSS源"""
    logger.info("开始测试英为财情RSS源...")
    
    # 英为财情的RSS源列表（从实际可用的源中选择）
    test_sources = [
        {
            "name": "英为财情-综合新闻",
            "url": "https://cn.investing.com/rss/news.rss",
            "description": "英为财情综合财经新闻"
        },
        {
            "name": "英为财情-股票新闻", 
            "url": "https://cn.investing.com/rss/news_285.rss",
            "description": "英为财情股票新闻"
        },
        {
            "name": "新浪财经-要闻",
            "url": "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=1686&k=&num=50&page=1",
            "description": "新浪财经要闻"
        }
    ]
    
    async with RSSAggregator() as aggregator:
        for source_config in test_sources:
            try:
                logger.info(f"\n测试RSS源: {source_config['name']}")
                logger.info(f"URL: {source_config['url']}")
                
                # 创建临时新闻源对象
                news_source = NewsSource(
                    name=source_config['name'],
                    description=source_config['description'],
                    source_type=NewsSourceType.RSS,
                    url=source_config['url'],
                    max_articles_per_fetch=5,  # 测试时只抓取5篇
                    language='zh',
                    region='CN',
                    status=NewsSourceStatus.ACTIVE
                )
                
                # 抓取数据
                articles = await aggregator.fetch_rss_feed(news_source)
                
                logger.info(f"✅ 成功抓取 {len(articles)} 篇文章")
                
                # 显示前3篇文章的标题
                for i, article in enumerate(articles[:3]):
                    logger.info(f"  {i+1}. {article.get('title', '无标题')[:100]}")
                    logger.info(f"     URL: {article.get('url', '无URL')}")
                    logger.info(f"     时间: {article.get('published_at', '无时间')}")
                    logger.info(f"     内容长度: {article.get('word_count', 0)} 字")
                
            except Exception as e:
                logger.error(f"❌ 抓取失败 {source_config['name']}: {e}")

async def test_database_initialization():
    """测试数据库初始化"""
    logger.info("开始测试数据库初始化...")
    
    try:
        initializer = NewsDBInitializer("sqlite+aiosqlite:///./test_news.db")
        
        # 清理并重新初始化
        await initializer.clean_and_reinitialize()
        
        logger.info("✅ 数据库初始化成功")
        
        # 获取初始化的新闻源数量
        async with initializer.SessionLocal() as session:
            from sqlalchemy import select
            query = select(NewsSource)
            result = await session.execute(query)
            sources = result.scalars().all()
            
            logger.info(f"📊 已配置 {len(sources)} 个默认新闻源:")
            for source in sources:
                logger.info(f"  - {source.name} ({source.source_type.value}) - {source.status.value}")
        
        await initializer.close()
        
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        raise

async def test_news_aggregator_manager():
    """测试新闻聚合管理器"""
    logger.info("开始测试新闻聚合管理器...")
    
    try:
        # 初始化数据库
        initializer = NewsDBInitializer("sqlite+aiosqlite:///./test_news.db")
        await initializer.initialize_all()
        
        # 创建聚合管理器
        manager = NewsAggregatorManager(initializer.SessionLocal)
        
        # 获取统计信息
        stats = await manager.get_aggregation_stats()
        logger.info(f"📊 聚合统计信息:")
        logger.info(f"  新闻源总数: {stats['source_stats']['total']}")
        logger.info(f"  活跃源数量: {stats['source_stats']['active']}")
        logger.info(f"  文章总数: {stats['article_stats']['total']}")
        
        # 测试单个源的连通性（英为财情）
        async with initializer.SessionLocal() as session:
            from sqlalchemy import select
            query = select(NewsSource).where(NewsSource.name.contains("英为财情"))
            result = await session.execute(query)
            investing_source = result.scalar_one_or_none()
            
            if investing_source:
                logger.info(f"\n测试英为财情源连通性: {investing_source.name}")
                test_result = await manager.test_source_connectivity(investing_source.id)
                
                if test_result['success']:
                    logger.info(f"✅ 连通性测试成功，抓取到 {test_result['articles_count']} 篇文章")
                    for article in test_result.get('sample_articles', []):
                        logger.info(f"  - {article['title'][:80]}...")
                else:
                    logger.error(f"❌ 连通性测试失败: {test_result['error']}")
        
        await initializer.close()
        
    except Exception as e:
        logger.error(f"❌ 聚合管理器测试失败: {e}")
        raise

async def main():
    """主测试函数"""
    logger.info("🚀 开始新闻聚合功能全面测试")
    
    try:
        # 1. 测试RSS源直接抓取
        await test_investing_rss_sources()
        
        # 2. 测试数据库初始化
        await test_database_initialization()
        
        # 3. 测试聚合管理器
        await test_news_aggregator_manager()
        
        logger.info("🎉 所有测试完成!")
        
    except Exception as e:
        logger.error(f"💥 测试过程中发生错误: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 