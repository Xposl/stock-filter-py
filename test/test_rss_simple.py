#!/usr/bin/env python3
"""
简化的RSS新闻抓取测试
测试英为财情等RSS源的连通性和数据抓取
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.news_aggregator.rss_aggregator import RSSAggregator
from core.models.news_source import NewsSource, NewsSourceType, NewsSourceStatus

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_single_rss_source(url: str, name: str) -> bool:
    """测试单个RSS源"""
    logger.info(f"\n🔍 测试RSS源: {name}")
    logger.info(f"   URL: {url}")
    
    try:
        # 创建临时新闻源对象（添加id字段用于测试）
        news_source = NewsSource(
            id=999,  # 临时测试ID
            name=name,
            description=f"测试源 - {name}",
            source_type=NewsSourceType.RSS,
            url=url,
            max_articles_per_fetch=3,  # 测试时只抓取3篇
            language='zh',
            region='CN',
            status=NewsSourceStatus.ACTIVE
        )
        
        # 使用RSS聚合器抓取
        async with RSSAggregator() as aggregator:
            articles = await aggregator.fetch_rss_feed(news_source)
            
            if articles:
                logger.info(f"✅ 成功! 抓取到 {len(articles)} 篇文章")
                
                # 显示文章标题
                for i, article in enumerate(articles):
                    title = article.get('title', '无标题')[:80]
                    pub_time = article.get('published_at', '无时间')
                    logger.info(f"   {i+1}. {title}...")
                    logger.info(f"      发布时间: {pub_time}")
                
                return True
            else:
                logger.warning(f"⚠️  RSS源连通但未获取到文章: {name}")
                return False
                
    except Exception as e:
        logger.error(f"❌ 抓取失败: {name} - {e}")
        return False

async def main():
    """主测试函数"""
    logger.info("🚀 开始RSS新闻源连通性测试")
    
    # 测试不同的RSS源
    test_sources = [
        # 英为财情
        ("https://cn.investing.com/rss/news.rss", "英为财情-综合新闻"),
        ("https://cn.investing.com/rss/news_285.rss", "英为财情-股票新闻"),
        
        # 第一财经（应该比较稳定）
        ("https://www.yicai.com/rss/news.xml", "第一财经-综合新闻"),
        
        # 新浪财经 
        ("https://feed.sina.com.cn/api/roll/get?pageid=153&lid=1686&k=&num=10&page=1", "新浪财经-快讯"),
        
        # 网易财经
        ("http://money.163.com/special/002557S6/rss_jsxw.xml", "网易财经-金融新闻"),
        
        # 凤凰财经
        ("http://finance.ifeng.com/rss/index.xml", "凤凰财经-综合"),
    ]
    
    success_count = 0
    total_count = len(test_sources)
    
    for url, name in test_sources:
        success = await test_single_rss_source(url, name)
        if success:
            success_count += 1
        
        # 请求间隔，避免请求过于频繁
        await asyncio.sleep(1)
    
    # 总结
    logger.info(f"\n📊 测试完成!")
    logger.info(f"   成功: {success_count}/{total_count} 个RSS源")
    logger.info(f"   成功率: {success_count/total_count*100:.1f}%")
    
    if success_count > 0:
        logger.info("✅ 至少有一个RSS源可用，新闻聚合功能基本正常")
    else:
        logger.error("❌ 所有RSS源都无法访问，需要检查网络或更换RSS源")

if __name__ == "__main__":
    asyncio.run(main()) 