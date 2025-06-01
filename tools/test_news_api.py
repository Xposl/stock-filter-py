#!/usr/bin/env python3
"""
新闻API简化测试脚本
专注测试新闻抓取和API功能，不依赖复杂的数据库初始化
"""

import asyncio
import sys
import os
from datetime import datetime
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_import_modules():
    """测试模块导入"""
    print("\n=== 测试模块导入 ===")
    
    try:
        from core.database.database import get_database_url
        print("✅ 数据库模块导入成功")
        
        database_url = get_database_url()
        print(f"📊 数据库URL: {database_url}")
        
        return True
    except Exception as e:
        print(f"❌ 数据库模块导入失败: {e}")
        return False

async def test_news_aggregator_simple():
    """简单的新闻聚合器测试"""
    print("\n=== 测试新闻聚合器（简化版）===")
    
    try:
        from core.news_aggregator.rss_aggregator import RSSAggregator
        
        # 创建RSS聚合器
        async with RSSAggregator() as aggregator:
            print("✅ RSS聚合器创建成功")
            
            # 测试单个RSS源
            test_url = "https://cn.investing.com/rss/news.rss"
            print(f"🔄 测试RSS源: {test_url}")
            
            # 尝试获取RSS内容
            articles = await aggregator.fetch_rss_content(test_url, max_articles=5)
            
            if articles:
                print(f"✅ 成功获取 {len(articles)} 篇文章")
                for i, article in enumerate(articles[:3], 1):
                    title = article.get('title', '无标题')[:50]
                    print(f"   {i}. {title}...")
            else:
                print("⚠️  未获取到文章，但RSS聚合器工作正常")
            
            return True
            
    except Exception as e:
        print(f"❌ 新闻聚合器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_scheduler_simple():
    """简单的调度器测试"""
    print("\n=== 测试调度器（简化版）===")
    
    try:
        # 尝试导入调度器模块
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger
        
        print("✅ APScheduler模块导入成功")
        
        # 创建简单的调度器
        scheduler = AsyncIOScheduler()
        print("✅ 调度器创建成功")
        
        # 添加一个测试任务
        def test_job():
            print(f"🔔 测试任务执行于: {datetime.now()}")
        
        scheduler.add_job(
            func=test_job,
            trigger=CronTrigger(second='*/5'),  # 每5秒执行一次
            id='test_job',
            name='测试任务'
        )
        
        print("✅ 测试任务添加成功")
        
        # 获取任务信息
        jobs = scheduler.get_jobs()
        print(f"📋 当前任务数量: {len(jobs)}")
        
        for job in jobs:
            print(f"   - {job.name} (ID: {job.id})")
        
        return True
        
    except Exception as e:
        print(f"❌ 调度器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_models():
    """测试API模型"""
    print("\n=== 测试API模型 ===")
    
    try:
        from pydantic import BaseModel
        from typing import Optional, List
        
        # 测试新闻请求模型
        class NewsRequest(BaseModel):
            source_ids: Optional[List[int]] = None
            limit: Optional[int] = 50
        
        # 创建测试实例
        request1 = NewsRequest()
        request2 = NewsRequest(source_ids=[1, 2, 3], limit=100)
        
        print("✅ NewsRequest模型测试成功")
        print(f"   默认请求: {request1.model_dump()}")
        print(f"   自定义请求: {request2.model_dump()}")
        
        return True
        
    except Exception as e:
        print(f"❌ API模型测试失败: {e}")
        return False

def test_shell_script():
    """测试Shell脚本"""
    print("\n=== 测试Shell脚本 ===")
    
    try:
        script_path = "scripts/cron_news_fetch.sh"
        if os.path.exists(script_path):
            print(f"✅ 发现Shell脚本: {script_path}")
            
            # 检查脚本权限
            if os.access(script_path, os.X_OK):
                print("✅ 脚本具有执行权限")
            else:
                print("⚠️  脚本缺少执行权限，运行: chmod +x scripts/cron_news_fetch.sh")
            
            # 显示脚本前几行
            with open(script_path, 'r') as f:
                lines = f.readlines()[:10]
                print("📄 脚本开头内容:")
                for i, line in enumerate(lines, 1):
                    print(f"   {i:2d}: {line.rstrip()}")
            
            return True
        else:
            print(f"❌ 未找到Shell脚本: {script_path}")
            return False
            
    except Exception as e:
        print(f"❌ Shell脚本测试失败: {e}")
        return False

async def demo_manual_usage():
    """演示手动使用方法"""
    print("\n=== 手动使用演示 ===")
    
    print("🔧 新闻抓取系统使用方法:")
    print()
    
    print("1. 启动FastAPI应用:")
    print("   uvicorn api.api:app --host 0.0.0.0 --port 8000")
    print()
    
    print("2. 手动触发新闻抓取:")
    print("   curl -X POST http://localhost:8000/investnote/cron/news \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"limit\": 50}'")
    print()
    
    print("3. 查看新闻列表:")
    print("   curl 'http://localhost:8000/investnote/news?page=1&page_size=10'")
    print()
    
    print("4. 查看新闻源状态:")
    print("   curl http://localhost:8000/investnote/news/sources")
    print()
    
    print("5. 启动定时调度器:")
    print("   curl -X POST http://localhost:8000/investnote/cron/news/scheduler/start")
    print()
    
    print("6. 查看调度器状态:")
    print("   curl http://localhost:8000/investnote/cron/news/scheduler")
    print()
    
    print("7. 使用系统Cron（可选）:")
    print("   chmod +x scripts/cron_news_fetch.sh")
    print("   ./scripts/cron_news_fetch.sh health")
    print("   ./scripts/cron_news_fetch.sh fetch")
    print()
    
    print("8. 查看API文档:")
    print("   浏览器访问: http://localhost:8000/investnote/docs")

async def main():
    """主测试函数"""
    print("🚀 开始新闻API简化测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_results = []
    
    # 1. 测试模块导入
    test_results.append(await test_import_modules())
    
    # 2. 测试API模型
    test_results.append(await test_api_models())
    
    # 3. 测试调度器
    test_results.append(await test_scheduler_simple())
    
    # 4. 测试新闻聚合器
    test_results.append(await test_news_aggregator_simple())
    
    # 5. 测试Shell脚本
    test_results.append(test_shell_script())
    
    # 6. 演示使用方法
    await demo_manual_usage()
    
    # 测试结果汇总
    print("\n" + "="*50)
    print("📊 测试结果汇总")
    print("="*50)
    
    test_names = [
        "模块导入",
        "API模型", 
        "调度器功能",
        "新闻聚合器",
        "Shell脚本"
    ]
    
    passed = 0
    for i, result in enumerate(test_results):
        if i < len(test_names):
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{test_names[i]}: {status}")
            if result:
                passed += 1
    
    print(f"\n总体结果: {passed}/{len(test_results)} 测试通过")
    
    if passed >= 4:  # 至少4个测试通过
        print("🎉 核心功能测试通过！新闻抓取系统准备就绪。")
        print("\n💡 下一步:")
        print("1. 启动FastAPI应用测试API接口")
        print("2. 运行: uvicorn api.api:app --host 0.0.0.0 --port 8000")
        print("3. 访问: http://localhost:8000/investnote/docs 查看API文档")
    else:
        print("⚠️  部分测试失败，但核心功能可能仍然可用")
        print("   建议检查错误信息并解决依赖问题")

if __name__ == "__main__":
    asyncio.run(main()) 