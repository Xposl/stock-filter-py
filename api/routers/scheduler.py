#!/usr/bin/env python3

"""
调度器和定时任务相关API路由
包含新闻定时抓取、调度器管理、股票数据更新等功能
"""

import math
import os
import time
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.database.database import get_database_url
from core.news_aggregator.news_aggregator_manager import NewsAggregatorManager
from core.scheduler.news_scheduler import (
    get_news_scheduler,
    start_news_scheduler,
    stop_news_scheduler,
)

from .news import NewsRequest, fetch_news_background_task

# 创建路由器 - 去掉prefix，保持原有路径结构
router = APIRouter(tags=["定时任务"])

# 加载环境变量
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "true").lower() == "true"

# 数据库会话工厂
_async_engine = None
_async_session_factory = None


def get_async_session_factory():
    """获取异步数据库会话工厂"""
    global _async_engine, _async_session_factory

    if _async_session_factory is None:
        database_url = get_database_url()
        _async_engine = create_async_engine(database_url, echo=False)
        _async_session_factory = async_sessionmaker(
            _async_engine, class_=AsyncSession, expire_on_commit=False
        )

    return _async_session_factory


@router.post("/cron/ticker/{market}/update")
async def cron_update_ticker_score(
    market: str,
    background_tasks: BackgroundTasks,
    # current_user: Dict[str, Any] = Depends(auth_required(["ADMIN"])) if AUTH_ENABLED else None
):
    """
    批量更新指定市场的ticker_score，分批处理，每批100只，间隔1秒，批次间隔1分钟。

    需要管理员权限访问。从ticker.py路由迁移而来，统一调度器管理。
    """
    from core.data_source_helper import DataSourceHelper
    from core.service.ticker_repository import TickerRepository

    # 市场映射
    market_map = {
        "hk": "HK",
        "zh": "SZ",  # 只用SZ/SH前缀区分A股
        "us": "US",
    }
    if market not in market_map:
        raise HTTPException(status_code=400, detail="market参数错误，只支持hk/zh/us")

    # 获取所有可用ticker
    repo = TickerRepository()
    tickers = repo.get_all_available()
    # 按市场过滤
    prefix = market_map[market]
    tickers = [
        t
        for t in tickers
        if t.code.startswith(prefix) or (market == "zh" and t.code.startswith("SH"))
    ]
    total = len(tickers)
    batch_size = 100
    batch_count = math.ceil(total / batch_size)

    def batch_update():
        ds = DataSourceHelper()
        for i in range(batch_count):
            batch = tickers[i * batch_size: (i + 1) * batch_size]
            if not batch:
                continue
            ds._update_tickers(batch)
            time.sleep(60)  # 每批间隔1分钟

    background_tasks.add_task(batch_update)
    return {
        "status": "started",
        "total": total,
        "batch_size": batch_size,
        "batch_count": batch_count,
    }


@router.post("/cron/news")
async def cron_fetch_news(
    background_tasks: BackgroundTasks,
    request: NewsRequest = NewsRequest(),
    # current_user: Dict[str, Any] = Depends(auth_required(["ADMIN"])) if AUTH_ENABLED else None
):
    """定时新闻抓取任务

    这个接口用于定时触发新闻抓取，可以通过cron定时任务调用
    支持指定新闻源或抓取所有活跃源
    """
    try:
        # 在后台任务中执行新闻抓取
        background_tasks.add_task(
            fetch_news_background_task,
            request.source_ids,
            request.limit or 50,  # 处理 None 值
        )

        return {
            "status": "success",
            "message": "新闻抓取任务已启动",
            "task_info": {
                "source_ids": request.source_ids or "all_active",
                "limit": request.limit,
                "started_at": datetime.now().isoformat(),
            },
        }
    except Exception as e:
        import traceback

        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail) from e


@router.get("/cron/news/status")
async def get_news_fetch_status():
    """获取新闻抓取状态和统计信息"""
    try:
        manager = NewsAggregatorManager()

        # 获取聚合统计信息
        stats = await manager.get_aggregation_stats()

        return {"status": "success", "data": stats}

    except Exception as e:
        import traceback

        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail) from e


@router.get("/cron/news/scheduler")
async def get_scheduler_status():
    """获取调度器状态和任务列表"""
    try:
        scheduler = await get_news_scheduler()
        jobs_info = scheduler.get_jobs()

        return {"status": "success", "data": jobs_info}

    except Exception as e:
        import traceback

        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail) from e


@router.post("/cron/news/scheduler/start")
async def start_scheduler():
    """启动新闻调度器"""
    try:
        scheduler = await start_news_scheduler()

        return {
            "status": "success",
            "message": "新闻调度器已启动",
            "data": {
                "started_at": datetime.now().isoformat(),
                "jobs": scheduler.get_jobs(),
            },
        }

    except Exception as e:
        import traceback

        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail) from e


@router.post("/cron/news/scheduler/stop")
async def stop_scheduler():
    """停止新闻调度器"""
    try:
        stop_news_scheduler()

        return {
            "status": "success",
            "message": "新闻调度器已停止",
            "data": {"stopped_at": datetime.now().isoformat()},
        }

    except Exception as e:
        import traceback

        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail) from e


@router.post("/cron/news/manual")
async def manual_fetch_news(request: NewsRequest = NewsRequest()):
    """手动触发新闻抓取（不依赖调度器）"""
    try:
        scheduler = await get_news_scheduler()
        result = await scheduler.trigger_manual_fetch(request.source_ids)

        return {"status": "success", "message": "手动新闻抓取完成", "data": result}

    except Exception as e:
        import traceback

        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail) from e
