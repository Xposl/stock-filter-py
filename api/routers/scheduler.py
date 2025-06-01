#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
调度器和定时任务相关API路由
包含新闻定时抓取、调度器管理等功能
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from core.auth.auth_middleware import auth_required
import os
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from core.news_aggregator.news_aggregator_manager import NewsAggregatorManager
from core.database.database import get_database_url
from core.scheduler.news_scheduler import get_news_scheduler, start_news_scheduler, stop_news_scheduler
from .news import fetch_news_background_task, NewsRequest

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
        _async_session_factory = sessionmaker(
            _async_engine, 
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    return _async_session_factory


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
            request.limit
        )
        
        return {
            "status": "success",
            "message": "新闻抓取任务已启动",
            "task_info": {
                "source_ids": request.source_ids or "all_active",
                "limit": request.limit,
                "started_at": datetime.now().isoformat()
            }
        }
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/cron/news/status")
async def get_news_fetch_status():
    """获取新闻抓取状态和统计信息"""
    try:
        session_factory = get_async_session_factory()
        manager = NewsAggregatorManager(session_factory)
        
        # 获取聚合统计信息
        stats = await manager.get_aggregation_stats()
        
        return {
            "status": "success",
            "data": stats
        }
        
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/cron/news/scheduler")
async def get_scheduler_status():
    """获取调度器状态和任务列表"""
    try:
        scheduler = await get_news_scheduler()
        jobs_info = scheduler.get_jobs()
        
        return {
            "status": "success",
            "data": jobs_info
        }
        
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


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
                "jobs": scheduler.get_jobs()
            }
        }
        
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


@router.post("/cron/news/scheduler/stop")
async def stop_scheduler():
    """停止新闻调度器"""
    try:
        stop_news_scheduler()
        
        return {
            "status": "success",
            "message": "新闻调度器已停止",
            "data": {
                "stopped_at": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


@router.post("/cron/news/manual")
async def manual_fetch_news(request: NewsRequest = NewsRequest()):
    """手动触发新闻抓取（不依赖调度器）"""
    try:
        scheduler = await get_news_scheduler()
        result = await scheduler.trigger_manual_fetch(request.source_ids)
        
        return {
            "status": "success",
            "message": "手动新闻抓取完成",
            "data": result
        }
        
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail) 