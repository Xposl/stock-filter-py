#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
完整新闻聚合测试
测试RSS和API新闻源的抓取功能，包括数据库操作
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.news_aggregator.rss_aggregator import RSSAggregator
from core.news_aggregator.api_aggregator import APIAggregator
from core.handler.news_source_handler import NewsSourceHandler
from core.handler.news_article_handler import NewsArticleHandler
from core.models.news_source import NewsSource, NewsSourceType, NewsSourceStatus

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_rss_sources():
    """测试RSS新闻源"""
    logger.info("🔍 开始测试RSS新闻源...")
    
    # 获取活跃的RSS源
    source_handler = NewsSourceHandler()
    sources = await source_handler.get_active_news_sources()
    rss_sources = [s for s in sources if s.source_type == NewsSourceType.RSS]
    
    if not rss_sources:
        logger.warning("⚠️  没有找到活跃的RSS源")
        return 0
    
    success_count = 0
    total_articles = 0
    
    async with RSSAggregator() as aggregator:
        for source in rss_sources[:5]:  # 只测试前5个源
            try:
                logger.info(f"测试RSS源: {source.name}")
                articles = await aggregator.fetch_rss_feed(source)
                
                if articles:
                    logger.info(f"  ✅ 成功抓取 {len(articles)} 篇文章")
                    success_count += 1
                    total_articles += len(articles)
                    
                    # 显示部分文章标题
                    for i, article in enumerate(articles[:3]):
                        title = article.get('title', '无标题')[:60]
                        logger.info(f"    {i+1}. {title}...")
                else:
                    logger.warning(f"  ⚠️  未获取到文章")
                    
            except Exception as e:
                logger.error(f"  ❌ 测试失败: {e}")
            
            # 间隔避免请求过频
            await asyncio.sleep(1)
    
    logger.info(f"📊 RSS源测试完成: 成功 {success_count}/{len(rss_sources)} 个源，共 {total_articles} 篇文章")
    return total_articles

async def test_api_sources():
    """测试API新闻源"""
    logger.info("🔍 开始测试API新闻源...")
    
    # 获取活跃的API源
    source_handler = NewsSourceHandler()
    sources = await source_handler.get_all_news_sources()
    api_sources = [s for s in sources if s.source_type == NewsSourceType.API and s.status == NewsSourceStatus.ACTIVE]
    
    if not api_sources:
        logger.warning("⚠️  没有找到活跃的API源")
        return 0
    
    success_count = 0
    total_articles = 0
    
    async with APIAggregator() as aggregator:
        for source in api_sources:
            try:
                logger.info(f"测试API源: {source.name}")
                articles = await aggregator.fetch_api_feed(source)
                
                if articles:
                    logger.info(f"  ✅ 成功抓取 {len(articles)} 篇文章")
                    success_count += 1
                    total_articles += len(articles)
                    
                    # 显示部分文章标题
                    for i, article in enumerate(articles[:3]):
                        title = article.get('title', '无标题')[:60]
                        logger.info(f"    {i+1}. {title}...")
                else:
                    logger.warning(f"  ⚠️  未获取到文章")
                    
            except Exception as e:
                logger.error(f"  ❌ 测试失败: {e}")
            
            # 间隔避免请求过频
            await asyncio.sleep(2)
    
    logger.info(f"📊 API源测试完成: 成功 {success_count}/{len(api_sources)} 个源，共 {total_articles} 篇文章")
    return total_articles

async def test_database_operations():
    """测试数据库操作"""
    logger.info("🔍 开始测试数据库操作...")
    
    try:
        # 测试新闻源操作
        source_handler = NewsSourceHandler()
        
        # 创建测试新闻源
        test_source_data = {
            "name": "测试RSS源",
            "description": "用于测试的RSS新闻源",
            "source_type": NewsSourceType.RSS,
            "url": "https://cn.investing.com/rss/news.rss",
            "update_frequency": 3600,
            "max_articles_per_fetch": 5,
            "language": "zh",
            "region": "CN",
            "status": NewsSourceStatus.ACTIVE
        }
        
        # 检查是否已存在
        existing = await source_handler.get_news_source_by_name(test_source_data["name"])
        if existing:
            logger.info("  测试源已存在，跳过创建")
            test_source = existing
        else:
            test_source = await source_handler.create_news_source(test_source_data)
            if test_source:
                logger.info(f"  ✅ 创建测试新闻源成功 (ID: {test_source.id})")
            else:
                logger.error("  ❌ 创建测试新闻源失败")
                return False
        
        # 测试新闻文章操作
        article_handler = NewsArticleHandler()
        
        # 模拟抓取文章并保存
        test_article_data = {
            "title": "测试新闻标题",
            "url": "https://example.com/test-news",
            "url_hash": "test_hash_123",
            "content": "这是一篇测试新闻的内容...",
            "summary": "测试新闻摘要",
            "source_id": test_source.id,
            "source_name": test_source.name,
            "language": "zh",
            "region": "CN"
        }
        
        # 检查是否已存在
        existing_article = await article_handler.repository.get_article_by_url_hash(test_article_data["url_hash"])
        if existing_article:
            logger.info("  测试文章已存在，跳过创建")
        else:
            test_article = await article_handler.create_news_article(test_article_data)
            if test_article:
                logger.info(f"  ✅ 创建测试文章成功 (ID: {test_article.id})")
            else:
                logger.error("  ❌ 创建测试文章失败")
        
        # 获取统计信息
        source_stats = await source_handler.get_news_source_stats()
        article_stats = await article_handler.get_article_stats()
        
        logger.info(f"  📊 新闻源统计: {source_stats}")
        logger.info(f"  📊 文章统计: {article_stats}")
        
        logger.info("✅ 数据库操作测试完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库操作测试失败: {e}")
        return False

async def test_full_workflow():
    """测试完整的新闻聚合工作流"""
    logger.info("🔍 开始测试完整工作流...")
    
    try:
        # 获取一个活跃的RSS源
        source_handler = NewsSourceHandler()
        article_handler = NewsArticleHandler()
        
        active_sources = await source_handler.get_active_news_sources()
        rss_sources = [s for s in active_sources if s.source_type == NewsSourceType.RSS]
        
        if not rss_sources:
            logger.warning("⚠️  没有活跃的RSS源可供测试")
            return False
        
        test_source = rss_sources[0]  # 使用第一个RSS源
        logger.info(f"使用测试源: {test_source.name}")
        
        # 1. 抓取新闻
        async with RSSAggregator() as aggregator:
            articles = await aggregator.fetch_rss_feed(test_source)
            
        if not articles:
            logger.warning("⚠️  未抓取到新闻文章")
            return False
        
        logger.info(f"✅ 抓取到 {len(articles)} 篇文章")
        
        # 2. 批量保存文章
        created_articles = await article_handler.batch_create_articles(articles)
        logger.info(f"✅ 成功保存 {len(created_articles)} 篇文章")
        
        # 3. 更新新闻源的抓取信息
        success = await source_handler.update_source_fetch_result(
            test_source.id, True, None, len(created_articles)
        )
        if success:
            logger.info("✅ 更新新闻源抓取信息成功")
        
        # 4. 查询最近的文章
        recent_articles = await article_handler.get_recent_articles(1, 10)  # 最近1小时，10篇
        logger.info(f"✅ 查询到 {len(recent_articles)} 篇最近文章")
        
        logger.info("🎉 完整工作流测试成功!")
        return True
        
    except Exception as e:
        logger.error(f"❌ 完整工作流测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    logger.info("🚀 开始新闻聚合系统综合测试")
    
    # 运行各项测试
    tests = [
        ("数据库操作测试", test_database_operations()),
        ("RSS源测试", test_rss_sources()),
        ("API源测试", test_api_sources()),
        ("完整工作流测试", test_full_workflow())
    ]
    
    results = {}
    
    for test_name, test_coro in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"🧪 {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_coro
            results[test_name] = result
            
            if isinstance(result, bool):
                status = "✅ 通过" if result else "❌ 失败"
            else:
                status = f"✅ 完成 (结果: {result})"
            
            logger.info(f"📊 {test_name}: {status}")
            
        except Exception as e:
            logger.error(f"❌ {test_name}执行异常: {e}")
            results[test_name] = False
        
        # 测试间隔
        await asyncio.sleep(1)
    
    # 总结
    logger.info(f"\n{'='*50}")
    logger.info("📊 测试结果总结")
    logger.info(f"{'='*50}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        if isinstance(result, bool):
            status = "✅ PASS" if result else "❌ FAIL"
            if result:
                passed += 1
        else:
            status = f"✅ PASS ({result})"
            passed += 1
        
        logger.info(f"  {test_name}: {status}")
    
    logger.info(f"\n🎯 总计: {passed}/{total} 测试通过")
    
    if passed == total:
        logger.info("🎉 所有测试通过! 新闻聚合系统运行正常")
    else:
        logger.warning("⚠️  部分测试失败，请检查相关功能")

if __name__ == "__main__":
    # 安装缺失的依赖
    try:
        import feedparser
        import newspaper
    except ImportError as e:
        logger.error(f"缺少依赖包: {e}")
        logger.info("请运行: pip install feedparser newspaper3k")
        sys.exit(1)
    
    asyncio.run(main()) 