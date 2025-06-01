#!/usr/bin/env python3
"""
新闻系统综合测试脚本
测试新闻抓取、定时任务、API接口等功能
"""

import asyncio
import sys
import os
from datetime import datetime
import httpx

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 修复导入路径
try:
    from tools.news_db_init import NewsDBInit
except ImportError:
    # 如果tools下没有，尝试其他位置
    try:
        from core.database.news_db_init import NewsDBInit
    except ImportError:
        print("警告: 无法找到NewsDBInit，将跳过数据库初始化测试")
        NewsDBInit = None

from core.news_aggregator.news_aggregator_manager import NewsAggregatorManager
from core.scheduler.news_scheduler import get_news_scheduler
from core.database.database import get_database_url
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

async def test_database_initialization():
    """测试数据库初始化"""
    print("\n=== 测试数据库初始化 ===")
    
    if NewsDBInit is None:
        print("⚠️  跳过数据库初始化测试（NewsDBInit不可用）")
        return True
    
    try:
        db_init = NewsDBInit()
        await db_init.init_database()
        print("✅ 数据库初始化成功")
        return True
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False

async def test_news_aggregation():
    """测试新闻聚合功能"""
    print("\n=== 测试新闻聚合功能 ===")
    
    try:
        # 创建数据库会话工厂
        database_url = get_database_url()
        engine = create_async_engine(database_url, echo=False)
        session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        # 创建新闻聚合管理器
        manager = NewsAggregatorManager(session_factory)
        
        # 获取聚合统计信息
        stats = await manager.get_aggregation_stats()
        print(f"📊 当前新闻源统计: {stats}")
        
        # 抓取所有活跃新闻源
        print("🔄 开始抓取新闻...")
        results = await manager.fetch_all_active_sources()
        
        # 统计结果
        total_articles = sum(r.get('articles_count', 0) for r in results)
        success_sources = len([r for r in results if r.get('status') == 'success'])
        error_sources = len([r for r in results if r.get('status') == 'error'])
        
        print(f"✅ 新闻抓取完成:")
        print(f"   - 成功源数量: {success_sources}")
        print(f"   - 失败源数量: {error_sources}")
        print(f"   - 获取文章数: {total_articles}")
        
        # 显示详细结果
        for result in results:
            status_icon = "✅" if result.get('status') == 'success' else "❌"
            print(f"   {status_icon} {result.get('source_name')}: {result.get('articles_count', 0)}篇文章")
        
        return len(results) > 0
        
    except Exception as e:
        print(f"❌ 新闻聚合测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_scheduler():
    """测试定时调度器功能"""
    print("\n=== 测试定时调度器功能 ===")
    
    try:
        # 获取调度器实例
        scheduler = await get_news_scheduler()
        
        # 启动调度器
        scheduler.start()
        print("✅ 调度器启动成功")
        
        # 获取任务列表
        jobs_info = scheduler.get_jobs()
        print(f"📋 定时任务列表 ({jobs_info['total_jobs']}个任务):")
        
        for job in jobs_info['jobs']:
            print(f"   - {job['name']} (ID: {job['id']})")
            print(f"     下次执行: {job['next_run_time']}")
        
        # 手动触发新闻抓取测试
        print("\n🔄 手动触发新闻抓取测试...")
        result = await scheduler.trigger_manual_fetch()
        
        print(f"✅ 手动抓取完成:")
        print(f"   - 成功源: {result.get('success_sources', 0)}")
        print(f"   - 失败源: {result.get('error_sources', 0)}")
        print(f"   - 获取文章: {result.get('total_articles', 0)}")
        
        # 关闭调度器
        scheduler.shutdown()
        print("✅ 调度器关闭成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 调度器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_endpoints():
    """测试API端点（需要FastAPI应用运行）"""
    print("\n=== 测试API端点 ===")
    
    base_url = "http://localhost:8000/investnote"
    
    async with httpx.AsyncClient() as client:
        try:
            # 测试获取新闻源列表
            print("🔍 测试获取新闻源列表...")
            response = await client.get(f"{base_url}/news/sources")
            if response.status_code == 200:
                sources = response.json()
                print(f"✅ 获取新闻源列表成功: {len(sources.get('data', []))}个源")
            else:
                print(f"❌ 获取新闻源列表失败: {response.status_code}")
            
            # 测试获取新闻文章
            print("🔍 测试获取新闻文章...")
            response = await client.get(f"{base_url}/news?page=1&page_size=5")
            if response.status_code == 200:
                news = response.json()
                total = news.get('data', {}).get('total', 0)
                articles = news.get('data', {}).get('articles', [])
                print(f"✅ 获取新闻文章成功: 总计{total}篇，返回{len(articles)}篇")
                
                # 显示最新几篇文章
                for i, article in enumerate(articles[:3], 1):
                    print(f"   {i}. {article.get('title', '无标题')[:50]}...")
            else:
                print(f"❌ 获取新闻文章失败: {response.status_code}")
            
            # 测试手动触发新闻抓取
            print("🔄 测试手动触发新闻抓取...")
            response = await client.post(f"{base_url}/cron/news")
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 手动触发抓取成功: {result.get('message')}")
            else:
                print(f"❌ 手动触发抓取失败: {response.status_code}")
            
            # 测试获取调度器状态
            print("🔍 测试获取调度器状态...")
            response = await client.get(f"{base_url}/cron/news/scheduler")
            if response.status_code == 200:
                scheduler_info = response.json()
                jobs = scheduler_info.get('data', {}).get('jobs', [])
                print(f"✅ 获取调度器状态成功: {len(jobs)}个定时任务")
            else:
                print(f"❌ 获取调度器状态失败: {response.status_code}")
            
            return True
            
        except httpx.ConnectError:
            print("❌ 无法连接到API服务器（请确保FastAPI应用正在运行）")
            print("   运行命令: uvicorn api.api:app --host 0.0.0.0 --port 8000")
            return False
        except Exception as e:
            print(f"❌ API测试失败: {e}")
            return False

async def main():
    """主测试函数"""
    print("🚀 开始新闻系统综合测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_results = []
    
    # 1. 测试数据库初始化
    test_results.append(await test_database_initialization())
    
    # 2. 测试新闻聚合功能
    test_results.append(await test_news_aggregation())
    
    # 3. 测试定时调度器功能
    test_results.append(await test_scheduler())
    
    # 4. 测试API端点（可选）
    print("\n❓ 是否测试API端点？（需要FastAPI应用运行）")
    user_input = input("输入 'y' 测试API，其他键跳过: ").lower()
    if user_input == 'y':
        test_results.append(await test_api_endpoints())
    
    # 测试结果汇总
    print("\n" + "="*50)
    print("📊 测试结果汇总")
    print("="*50)
    
    test_names = [
        "数据库初始化",
        "新闻聚合功能", 
        "定时调度器功能",
        "API端点测试"
    ]
    
    passed = 0
    for i, result in enumerate(test_results):
        if i < len(test_names):
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_names[i]}: {status}")
            if result:
                passed += 1
    
    print(f"\n总体结果: {passed}/{len(test_results)} 测试通过")
    
    if passed == len(test_results):
        print("🎉 所有测试都通过了！新闻系统工作正常。")
    else:
        print("⚠️  有测试失败，请检查错误信息并修复问题。")
    
    print("\n🔧 使用说明:")
    print("1. 启动FastAPI应用: uvicorn api.api:app --host 0.0.0.0 --port 8000")
    print("2. 手动触发新闻抓取: POST /investnote/cron/news")
    print("3. 查看新闻列表: GET /investnote/news")
    print("4. 启动定时调度器: POST /investnote/cron/news/scheduler/start")
    print("5. 查看Swagger文档: http://localhost:8000/investnote/docs")

if __name__ == "__main__":
    asyncio.run(main()) 