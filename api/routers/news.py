#!/usr/bin/env python3

"""
新闻相关API路由
包含新闻文章查询、新闻源管理、新闻抓取等功能
"""

import os
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.database.database import get_database_url
from core.news_aggregator.news_aggregator_manager import NewsAggregatorManager
from core.service.news_article_repository import NewsArticleRepository
from core.service.news_source_repository import NewsSourceRepository

# 创建路由器 - 去掉prefix，保持原有路径结构
router = APIRouter(tags=["新闻"])

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


# 新闻相关的Pydantic模型
class NewsRequest(BaseModel):
    source_ids: Optional[list[int]] = None  # 指定新闻源ID，为空则抓取所有活跃源
    limit: Optional[int] = 50  # 返回文章数量限制


class NewsQueryRequest(BaseModel):
    page: int = 1
    page_size: int = 20
    search: Optional[str] = None  # 搜索关键词
    source_id: Optional[int] = None  # 指定新闻源
    hours: Optional[int] = 24  # 获取多少小时内的新闻
    status: Optional[str] = None  # 文章状态筛选


@router.get("/news")
async def get_news_articles(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    source_id: Optional[int] = None,
    hours: Optional[int] = 24,
    status: Optional[str] = None,
):
    """获取新闻文章列表

    支持分页、搜索、按新闻源筛选、按时间范围筛选
    """
    try:
        # 使用Repository模式查询新闻文章
        repository = NewsArticleRepository()
        articles, total = await repository.query_articles(
            page=page,
            page_size=page_size,
            search=search,
            source_id=source_id,
            hours=hours,
            status=status,
        )

        # 转换为字典
        articles_data = []
        for article in articles:
            articles_data.append(
                {
                    "id": article.id,
                    "title": article.title,
                    "url": article.url,
                    "content": article.content[:200] + "..."
                    if article.content and len(article.content) > 200
                    else article.content,
                    "author": article.author,
                    "published_at": article.published_at.isoformat()
                    if article.published_at
                    else None,
                    "created_at": article.created_at.isoformat()
                    if article.created_at
                    else None,
                    "source_id": article.source_id,
                    "status": article.status,
                    "importance_score": article.importance_score,
                    "market_relevance_score": article.market_relevance_score,
                    "stock_symbols": getattr(article, "stock_symbols", None),
                    "category": article.category,
                    "sentiment_score": article.sentiment_score,
                }
            )

        # 计算分页信息
        total_pages = (total + page_size - 1) // page_size

        return {
            "status": "success",
            "data": {
                "articles": articles_data,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1,
                },
            },
        }

    except Exception as e:
        import traceback

        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail) from e


@router.get("/news/sources")
async def get_news_sources():
    """获取新闻源列表"""
    try:
        # 使用Repository模式获取新闻源数据
        repository = NewsSourceRepository()
        sources = await repository.get_all_news_sources()

        sources_data = []
        for source in sources:
            sources_data.append(
                {
                    "id": source.id,
                    "name": source.name,
                    "url": source.url,
                    "source_type": source.source_type,
                    "status": source.status,
                    "description": source.description,
                    "last_fetch_at": source.last_fetch_time.isoformat()
                    if source.last_fetch_time
                    else None,
                    "last_article_count": getattr(source, "last_article_count", 0),
                    "total_articles": source.total_articles_fetched,
                    "error_count": getattr(source, "error_count", 0),
                    "created_at": source.created_at.isoformat()
                    if source.created_at
                    else None,
                    "updated_at": source.updated_at.isoformat()
                    if source.updated_at
                    else None,
                }
            )

        return {"status": "success", "data": sources_data}

    except Exception as e:
        import traceback

        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail) from e


@router.get("/news/{article_id}")
async def get_news_article(article_id: int):
    """获取单篇新闻文章的详细信息"""
    try:
        # 使用Repository模式获取文章
        repository = NewsArticleRepository()
        article = await repository.get_article_by_id(article_id)

        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")

        return {
            "status": "success",
            "data": {
                "id": article.id,
                "title": article.title,
                "url": article.url,
                "content": article.content,
                "author": article.author,
                "published_at": article.published_at.isoformat()
                if article.published_at
                else None,
                "created_at": article.created_at.isoformat()
                if article.created_at
                else None,
                "updated_at": article.updated_at.isoformat()
                if article.updated_at
                else None,
                "source_id": article.source_id,
                "status": article.status,
                "importance_score": article.importance_score,
                "market_relevance_score": article.market_relevance_score,
                "stock_symbols": getattr(article, "stock_symbols", None),
                "category": article.category,
                "entities": article.entities,
                "keywords": article.keywords,
                "sentiment_score": article.sentiment_score,
                "topics": article.topics,
                "word_count": article.word_count,
                "read_time_minutes": article.read_time_minutes,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback

        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail) from e


async def fetch_news_background_task(
    source_ids: Optional[list[int]] = None, limit: int = 50
):
    """后台新闻抓取任务"""
    try:
        # 使用新的初始化方式，不需要session_factory
        manager = NewsAggregatorManager()

        if source_ids:
            # 抓取指定新闻源
            results = await manager.fetch_specific_sources(source_ids)
        else:
            # 抓取所有活跃新闻源
            results = await manager.fetch_all_active_sources()

        # 记录任务执行结果
        total_articles = sum(r.get("articles_count", 0) for r in results)
        success_sources = len([r for r in results if r.get("status") == "success"])
        error_sources = len([r for r in results if r.get("status") == "error"])

        print(
            f"新闻抓取任务完成: {success_sources}个源成功, {error_sources}个源失败, 共获取{total_articles}篇文章")

        return {
            "success_sources": success_sources,
            "error_sources": error_sources,
            "total_articles": total_articles,
            "results": results,
        }

    except Exception as e:
        print(f"新闻抓取任务失败: {str(e)}")
        import traceback

        traceback.print_exc()
        return {"error": str(e)}
