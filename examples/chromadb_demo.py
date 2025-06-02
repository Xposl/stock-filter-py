#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ChromaDB 使用示例
演示如何在 InvestNote-py 项目中使用向量数据库
"""

import asyncio
import logging
import sys
import os
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ai_agents.vector_store import ChromaNewsStore, get_chroma_store

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChromaDBDemo:
    """ChromaDB使用演示"""
    
    def __init__(self):
        self.store = get_chroma_store()
    
    async def basic_usage_demo(self):
        """基础使用演示"""
        print("=" * 60)
        print("ChromaDB 基础使用演示")
        print("=" * 60)
        
        # 1. 添加新闻文章
        print("\n1. 添加新闻文章到向量数据库...")
        
        sample_articles = [
            {
                "id": 1,
                "title": "苹果公司发布最新财报，营收创历史新高",
                "content": "苹果公司今日发布了2024年第四季度财报，营收达到1200亿美元，同比增长15%。iPhone销量表现强劲，推动公司整体业绩增长。",
                "source": "财经新闻网"
            },
            {
                "id": 2,
                "title": "特斯拉股价大涨，电动车市场前景看好",
                "content": "特斯拉股价今日上涨8%，达到每股300美元。分析师认为电动车市场将继续快速增长，特斯拉有望受益于这一趋势。",
                "source": "汽车资讯"
            },
            {
                "id": 3,
                "title": "微软云服务业务增长强劲，AI应用推动营收",
                "content": "微软Azure云服务在本季度实现了40%的同比增长。AI相关服务和产品成为新的增长引擎，为公司带来了可观的营收。",
                "source": "科技日报"
            },
            {
                "id": 4,
                "title": "比特币价格突破新高，加密货币市场活跃",
                "content": "比特币价格今日突破50000美元大关，创下年内新高。加密货币市场整体表现活跃，投资者情绪乐观。",
                "source": "区块链资讯"
            }
        ]
        
        for article in sample_articles:
            success = await self.store.add_news_article(
                article_id=article["id"],
                title=article["title"],
                content=article["content"],
                source=article["source"],
                metadata={"demo": True}
            )
            if success:
                print(f"✅ 添加文章: {article['title'][:30]}...")
            else:
                print(f"❌ 添加失败: {article['title'][:30]}...")
    
    async def similarity_search_demo(self):
        """相似性搜索演示"""
        print("\n2. 语义相似性搜索...")
        
        # 搜索与"苹果财报"相关的文章
        query = "苹果公司财务业绩"
        print(f"\n🔍 搜索查询: '{query}'")
        
        results = await self.store.search_similar_articles(
            query_text=query,
            limit=3,
            similarity_threshold=0.3
        )
        
        print(f"找到 {len(results)} 篇相似文章:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. 标题: {result['title']}")
            print(f"   相似度: {result['similarity_score']:.3f}")
            print(f"   来源: {result['source']}")
            print(f"   预览: {result['text_preview'][:100]}...")
    
    async def keyword_search_demo(self):
        """关键词搜索演示"""
        print("\n3. 关键词搜索...")
        
        keywords = ["AI", "人工智能", "云服务"]
        print(f"\n🔍 关键词搜索: {keywords}")
        
        results = await self.store.search_by_keywords(
            keywords=keywords,
            limit=5
        )
        
        print(f"找到 {len(results)} 篇相关文章:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. 标题: {result['title']}")
            print(f"   来源: {result['source']}")
    
    async def batch_operations_demo(self):
        """批量操作演示"""
        print("\n4. 批量添加文章...")
        
        batch_articles = [
            {
                "id": 5,
                "title": "谷歌推出新一代AI芯片，性能提升显著",
                "content": "谷歌发布了最新的TPU AI芯片，相比上一代性能提升了300%。这将进一步加强谷歌在AI领域的竞争优势。",
                "source": "AI科技报",
                "metadata": {"category": "AI", "batch": True}
            },
            {
                "id": 6,
                "title": "亚马逊AWS收入增长，云计算市场竞争激烈",
                "content": "亚马逊AWS在本季度实现了25%的收入增长。云计算市场竞争日趋激烈，各大厂商纷纷加大投入。",
                "source": "云计算周刊",
                "metadata": {"category": "云计算", "batch": True}
            }
        ]
        
        result = await self.store.batch_add_articles(batch_articles)
        print(f"批量添加结果: {result}")
    
    async def stats_demo(self):
        """统计信息演示"""
        print("\n5. 数据库统计信息...")
        
        stats = self.store.get_collection_stats()
        print(f"\n📊 ChromaDB 统计:")
        print(f"   集合名称: {stats['collection_name']}")
        print(f"   文档数量: {stats['document_count']}")
        print(f"   存储路径: {stats['db_path']}")
        print(f"   嵌入模型: {stats['embedding_model']}")
        print(f"   状态: {stats['status']}")
    
    async def article_management_demo(self):
        """文章管理演示"""
        print("\n6. 文章管理...")
        
        # 获取特定文章
        article = await self.store.get_article_by_id(1)
        if article:
            print(f"\n📖 文章详情 (ID: 1):")
            print(f"   标题: {article['title']}")
            print(f"   来源: {article['source']}")
            print(f"   内容预览: {article['content'][:100]}...")
        
        # 删除文章
        print(f"\n🗑️ 删除文章 (ID: 6)...")
        deleted = await self.store.delete_article(6)
        print(f"删除结果: {'成功' if deleted else '失败'}")
    
    async def semantic_analysis_demo(self):
        """语义分析演示"""
        print("\n7. 高级语义分析...")
        
        # 投资主题相关性分析
        investment_queries = [
            "科技股投资机会",
            "新能源汽车前景",
            "AI人工智能发展趋势"
        ]
        
        for query in investment_queries:
            print(f"\n💡 投资主题: '{query}'")
            results = await self.store.search_similar_articles(
                query_text=query,
                limit=2,
                similarity_threshold=0.4
            )
            
            if results:
                print(f"   相关新闻 ({len(results)} 篇):")
                for result in results:
                    print(f"   • {result['title']} (相似度: {result['similarity_score']:.3f})")
            else:
                print("   未找到相关新闻")

async def main():
    """主函数"""
    print("🚀 ChromaDB 向量数据库使用演示")
    print("InvestNote-py 项目 - 金融新闻语义分析")
    
    demo = ChromaDBDemo()
    
    try:
        # 运行所有演示
        await demo.basic_usage_demo()
        await demo.similarity_search_demo()
        await demo.keyword_search_demo()
        await demo.batch_operations_demo()
        await demo.stats_demo()
        await demo.article_management_demo()
        await demo.semantic_analysis_demo()
        
        print("\n" + "=" * 60)
        print("✅ ChromaDB 演示完成!")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"演示过程中出现错误: {e}")
        print(f"\n❌ 演示失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())
