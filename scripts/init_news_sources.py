#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
新闻源初始化脚本
自动插入常用的金融新闻源到数据库
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.handler.news_source_handler import NewsSourceHandler
from core.models.news_source import NewsSourceType, NewsSourceStatus

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 预定义的新闻源配置
FINANCIAL_NEWS_SOURCES = [
    # Investing.com 相关源
    {
        "name": "英为财情-综合新闻",
        "description": "英为财情(Investing.com)综合金融新闻RSS源",
        "source_type": NewsSourceType.RSS,
        "url": "https://cn.investing.com/rss/news.rss",
        "update_frequency": 1800,  # 30分钟
        "max_articles_per_fetch": 20,
        "language": "zh",
        "region": "CN",
        "status": NewsSourceStatus.ACTIVE
    },
    {
        "name": "英为财情-股票新闻",
        "description": "英为财情(Investing.com)股票市场新闻RSS源",
        "source_type": NewsSourceType.RSS,
        "url": "https://cn.investing.com/rss/news_285.rss",
        "update_frequency": 1800,  # 30分钟
        "max_articles_per_fetch": 15,
        "language": "zh",
        "region": "CN",
        "status": NewsSourceStatus.ACTIVE
    },
    {
        "name": "英为财情-外汇新闻",
        "description": "英为财情(Investing.com)外汇市场新闻RSS源",
        "source_type": NewsSourceType.RSS,
        "url": "https://cn.investing.com/rss/news_1.rss",
        "update_frequency": 3600,  # 1小时
        "max_articles_per_fetch": 10,
        "language": "zh",
        "region": "CN",
        "status": NewsSourceStatus.ACTIVE
    },
    {
        "name": "英为财情-商品新闻",
        "description": "英为财情(Investing.com)商品市场新闻RSS源",
        "source_type": NewsSourceType.RSS,
        "url": "https://cn.investing.com/rss/news_49.rss",
        "update_frequency": 3600,  # 1小时
        "max_articles_per_fetch": 10,
        "language": "zh",
        "region": "CN",
        "status": NewsSourceStatus.ACTIVE
    },
    
    # 国内主要财经媒体
    {
        "name": "第一财经-综合新闻",
        "description": "第一财经官方RSS新闻源",
        "source_type": NewsSourceType.RSS,
        "url": "https://www.yicai.com/rss/news.xml",
        "update_frequency": 1800,  # 30分钟
        "max_articles_per_fetch": 25,
        "language": "zh",
        "region": "CN",
        "status": NewsSourceStatus.ACTIVE
    },
    {
        "name": "新浪财经-要闻",
        "description": "新浪财经重要新闻RSS源",
        "source_type": NewsSourceType.RSS,
        "url": "https://feed.sina.com.cn/api/roll/get?pageid=153&lid=1686&k=&num=20&page=1",
        "update_frequency": 1200,  # 20分钟
        "max_articles_per_fetch": 20,
        "language": "zh",
        "region": "CN",
        "status": NewsSourceStatus.ACTIVE
    },
    {
        "name": "网易财经-股票",
        "description": "网易财经股票新闻RSS源",
        "source_type": NewsSourceType.RSS,
        "url": "http://money.163.com/special/002557S6/rss_jsxw.xml",
        "update_frequency": 1800,  # 30分钟
        "max_articles_per_fetch": 15,
        "language": "zh",
        "region": "CN",
        "status": NewsSourceStatus.ACTIVE
    },
    {
        "name": "凤凰财经-综合",
        "description": "凤凰财经综合新闻RSS源",
        "source_type": NewsSourceType.RSS,
        "url": "http://finance.ifeng.com/rss/index.xml",
        "update_frequency": 2400,  # 40分钟
        "max_articles_per_fetch": 15,
        "language": "zh",
        "region": "CN",
        "status": NewsSourceStatus.ACTIVE
    },
    
    # 雪球相关 (注：雪球没有公开RSS，这里使用API方式)
    {
        "name": "雪球-热门话题",
        "description": "雪球社区热门投资话题和讨论",
        "source_type": NewsSourceType.API,
        "url": "https://xueqiu.com/statuses/hot/listV2.json",
        "update_frequency": 1800,  # 30分钟
        "max_articles_per_fetch": 20,
        "language": "zh",
        "region": "CN",
        "status": NewsSourceStatus.INACTIVE  # 先设为不活跃，需要实现专门的抓取逻辑
    },
    {
        "name": "雪球-今日话题",
        "description": "雪球今日热门投资话题",
        "source_type": NewsSourceType.API,
        "url": "https://xueqiu.com/v4/statuses/public_timeline_by_category.json",
        "update_frequency": 1800,  # 30分钟
        "max_articles_per_fetch": 15,
        "language": "zh",
        "region": "CN",
        "status": NewsSourceStatus.INACTIVE  # 先设为不活跃
    },
    
    # 东方财富相关
    {
        "name": "东方财富-股票资讯",
        "description": "东方财富网股票资讯",
        "source_type": NewsSourceType.API,
        "url": "http://feed.eastmoney.com/api/api/get/getfeedlist",
        "update_frequency": 1800,  # 30分钟
        "max_articles_per_fetch": 20,
        "language": "zh",
        "region": "CN",
        "status": NewsSourceStatus.INACTIVE  # 先设为不活跃，需要实现专门的抓取逻辑
    },
    {
        "name": "东方财富-研报中心",
        "description": "东方财富研究报告中心",
        "source_type": NewsSourceType.API,
        "url": "http://reportapi.eastmoney.com/report/list",
        "update_frequency": 3600,  # 1小时
        "max_articles_per_fetch": 10,
        "language": "zh",
        "region": "CN",
        "status": NewsSourceStatus.INACTIVE  # 先设为不活跃
    },
    
    # 其他重要财经媒体
    {
        "name": "财联社-快讯",
        "description": "财联社实时财经快讯",
        "source_type": NewsSourceType.RSS,
        "url": "https://www.cls.cn/rss/telegraph",
        "update_frequency": 900,  # 15分钟
        "max_articles_per_fetch": 30,
        "language": "zh",
        "region": "CN",
        "status": NewsSourceStatus.ACTIVE
    },
    {
        "name": "证券时报-新闻",
        "description": "证券时报官方新闻RSS源",
        "source_type": NewsSourceType.RSS,
        "url": "http://www.stcn.com/rss/news.xml",
        "update_frequency": 1800,  # 30分钟
        "max_articles_per_fetch": 15,
        "language": "zh",
        "region": "CN",
        "status": NewsSourceStatus.ACTIVE
    }
]

async def init_news_sources():
    """初始化新闻源"""
    try:
        logger.info("🚀 开始初始化金融新闻源...")
        
        # 创建新闻源处理器
        handler = NewsSourceHandler()
        
        created_count = 0
        skipped_count = 0
        failed_count = 0
        
        for source_config in FINANCIAL_NEWS_SOURCES:
            try:
                logger.info(f"处理新闻源: {source_config['name']}")
                
                # 检查是否已存在
                existing = await handler.get_news_source_by_name(source_config['name'])
                if existing:
                    logger.info(f"  ⏭️  已存在，跳过: {source_config['name']}")
                    skipped_count += 1
                    continue
                
                # 创建新闻源
                result = await handler.create_news_source(source_config)
                if result:
                    logger.info(f"  ✅ 创建成功: {source_config['name']} (ID: {result.id})")
                    created_count += 1
                else:
                    logger.error(f"  ❌ 创建失败: {source_config['name']}")
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"  ❌ 处理新闻源失败 {source_config['name']}: {e}")
                failed_count += 1
                continue
        
        # 输出统计信息
        logger.info(f"\n📊 初始化完成统计:")
        logger.info(f"  ✅ 新创建: {created_count} 个")
        logger.info(f"  ⏭️  已存在: {skipped_count} 个")
        logger.info(f"  ❌ 失败: {failed_count} 个")
        logger.info(f"  📝 总计: {len(FINANCIAL_NEWS_SOURCES)} 个")
        
        # 显示活跃源统计
        active_sources = await handler.get_active_news_sources()
        logger.info(f"  🔄 当前活跃源: {len(active_sources)} 个")
        
        return {
            "created": created_count,
            "skipped": skipped_count,
            "failed": failed_count,
            "total": len(FINANCIAL_NEWS_SOURCES),
            "active": len(active_sources)
        }
        
    except Exception as e:
        logger.error(f"初始化新闻源异常: {e}")
        return None

async def list_current_sources():
    """列出当前数据库中的新闻源"""
    try:
        logger.info("\n📋 当前数据库中的新闻源:")
        
        handler = NewsSourceHandler()
        sources = await handler.get_all_news_sources(limit=100)
        
        if not sources:
            logger.info("  (无新闻源)")
            return
        
        for source in sources:
            status_emoji = "🟢" if source.status == NewsSourceStatus.ACTIVE else "🔴"
            type_emoji = "📡" if source.source_type == NewsSourceType.RSS else "🔗"
            
            logger.info(f"  {status_emoji} {type_emoji} [{source.id:2d}] {source.name}")
            logger.info(f"      类型: {source.source_type.value} | 状态: {source.status.value}")
            logger.info(f"      URL: {source.url}")
            logger.info(f"      抓取间隔: {source.update_frequency}秒 | 最大文章数: {source.max_articles_per_fetch}")
            logger.info("")
        
        logger.info(f"总计: {len(sources)} 个新闻源")
        
    except Exception as e:
        logger.error(f"列出新闻源失败: {e}")

async def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        # 只列出当前源
        await list_current_sources()
    else:
        # 初始化新闻源
        result = await init_news_sources()
        
        if result:
            # 列出当前源
            await list_current_sources()
            
            logger.info("\n🎉 新闻源初始化完成!")
            logger.info("💡 提示:")
            logger.info("  - RSS类型的源可以直接使用")
            logger.info("  - API类型的源需要实现专门的抓取逻辑")
            logger.info("  - 使用 --list 参数可以只查看当前源列表")
        else:
            logger.error("❌ 新闻源初始化失败!")

if __name__ == "__main__":
    asyncio.run(main()) 