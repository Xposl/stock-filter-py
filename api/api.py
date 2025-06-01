from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from core.data_source_helper import DataSourceHelper
from .models import PageRequest
from core.auth.auth_middleware import auth_required
import time
import os
from fastapi.requests import Request
from core.service.api_log_repository import ApiLogRepository
from core.models.api_log import ApiLog
import traceback as tb

# 新增新闻相关导入
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from core.models.news_article import NewsArticle, ArticleStatus
from core.models.news_source import NewsSource, NewsSourceStatus
from core.news_aggregator.news_aggregator_manager import NewsAggregatorManager
from core.database.database import get_database_url
from core.service.news_source_repository import NewsSourceRepository
from core.service.news_article_repository import NewsArticleRepository
from sqlalchemy import select, desc

# 新增调度器相关导入
from core.scheduler.news_scheduler import get_news_scheduler, start_news_scheduler, stop_news_scheduler

app = FastAPI(
    title="InvestNote API",
    description="Investment notes and analysis API",
    root_path="/investnote",  # 添加根路径前缀
    docs_url="/docs",  # Swagger文档路径
    redoc_url="/redoc",  # ReDoc文档路径
)

# 加载环境变量
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "true").lower() == "true"

dataSource = DataSourceHelper()

# 新增：数据库会话工厂
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

# 新增：新闻相关的Pydantic模型
class NewsRequest(BaseModel):
    source_ids: Optional[List[int]] = None  # 指定新闻源ID，为空则抓取所有活跃源
    limit: Optional[int] = 50  # 返回文章数量限制

class NewsQueryRequest(BaseModel):
    page: int = 1
    page_size: int = 20
    search: Optional[str] = None  # 搜索关键词
    source_id: Optional[int] = None  # 指定新闻源
    hours: Optional[int] = 24  # 获取多少小时内的新闻
    status: Optional[str] = None  # 文章状态筛选

class TickerRequest(BaseModel):
    market: str  # 'hk', 'zh', 'us'
    code: str
    is_real_time: Optional[bool] = False
    days: Optional[int] = 250

class TickerQuery(BaseModel):
    market: str  # 'hk', 'zh', 'us'
    code: str
    days: Optional[int] = 250

@app.get("/")
async def root():
    return {"message": "InvestNote API Service"}

@app.get("/me")
async def get_current_user(current_user: Dict[str, Any] = Depends(auth_required())):
    """获取当前认证用户的信息
    
    需要有效的认证Token
    """
    return {
        "status": "success",
        "data": current_user
    }

# 新增：新闻相关API端点

@app.post("/cron/news")
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

@app.get("/news")
async def get_news_articles(
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    source_id: Optional[int] = None,
    hours: Optional[int] = 24,
    status: Optional[str] = None
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
            status=status
        )
        
        # 转换为字典
        articles_data = []
        for article in articles:
            articles_data.append({
                "id": article.id,
                "title": article.title,
                "url": article.url,
                "content": article.content[:200] + "..." if article.content and len(article.content) > 200 else article.content,
                "author": article.author,
                "published_at": article.published_at.isoformat() if article.published_at else None,
                "created_at": article.created_at.isoformat() if article.created_at else None,
                "source_id": article.source_id,
                "status": article.status,
                "importance_score": article.importance_score,
                "market_relevance_score": article.market_relevance_score,
                "stock_symbols": getattr(article, 'stock_symbols', None),
                "category": article.category,
                "sentiment_score": article.sentiment_score
            })
        
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
                    "has_prev": page > 1
                }
            }
        }
        
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)

@app.get("/news/sources")
async def get_news_sources():
    """获取新闻源列表"""
    try:
        # 使用Repository模式获取新闻源数据
        repository = NewsSourceRepository()
        sources = await repository.get_all_news_sources()
        
        sources_data = []
        for source in sources:
            sources_data.append({
                "id": source.id,
                "name": source.name,
                "url": source.url,
                "source_type": source.source_type,
                "status": source.status,
                "description": source.description,
                "last_fetch_at": source.last_fetch_time.isoformat() if source.last_fetch_time else None,
                "last_article_count": getattr(source, 'last_article_count', 0),
                "total_articles": source.total_articles_fetched,
                "error_count": getattr(source, 'error_count', 0),
                "created_at": source.created_at.isoformat() if source.created_at else None,
                "updated_at": source.updated_at.isoformat() if source.updated_at else None
            })
        
        return {
            "status": "success",
            "data": sources_data
        }
        
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)

@app.get("/news/{article_id}")
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
                "published_at": article.published_at.isoformat() if article.published_at else None,
                "created_at": article.created_at.isoformat() if article.created_at else None,
                "updated_at": article.updated_at.isoformat() if article.updated_at else None,
                "source_id": article.source_id,
                "status": article.status,
                "importance_score": article.importance_score,
                "market_relevance_score": article.market_relevance_score,
                "stock_symbols": getattr(article, 'stock_symbols', None),
                "category": article.category,
                "entities": article.entities,
                "keywords": article.keywords,
                "sentiment_score": article.sentiment_score,
                "topics": article.topics,
                "word_count": article.word_count,
                "read_time_minutes": article.read_time_minutes
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)

@app.get("/cron/news/status")
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

@app.get("/cron/news/scheduler")
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

@app.post("/cron/news/scheduler/start")
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

@app.post("/cron/news/scheduler/stop")
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

@app.post("/cron/news/manual")
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

async def fetch_news_background_task(source_ids: Optional[List[int]] = None, limit: int = 50):
    """后台新闻抓取任务"""
    try:
        session_factory = get_async_session_factory()
        manager = NewsAggregatorManager(session_factory)
        
        if source_ids:
            # 抓取指定新闻源
            results = await manager.fetch_specific_sources(source_ids)
        else:
            # 抓取所有活跃新闻源
            results = await manager.fetch_all_active_sources()
        
        # 记录任务执行结果
        total_articles = sum(r.get('articles_count', 0) for r in results)
        success_sources = len([r for r in results if r.get('status') == 'success'])
        error_sources = len([r for r in results if r.get('status') == 'error'])
        
        print(f"新闻抓取任务完成: {success_sources}个源成功, {error_sources}个源失败, 共获取{total_articles}篇文章")
        
        return {
            "success_sources": success_sources,
            "error_sources": error_sources,
            "total_articles": total_articles,
            "results": results
        }
        
    except Exception as e:
        print(f"新闻抓取任务失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@app.post("/pages")
async def get_ticker_pages(
    request: PageRequest
):
    """获取股票列表，支持分页、搜索和排序
    
    如果启用了鉴权，则只有认证用户可以访问
    """
    try:
        from core.service.ticker_repository import TickerRepository
        from datetime import datetime
        import os
        
        # 获取ticker数据
        repo = TickerRepository()
        
        # 获取占位符类型
        DB_TYPE = os.getenv('DB_TYPE', 'sqlite').lower()
        PLACEHOLDER = '?' if DB_TYPE == 'sqlite' else '%s'
        
        # 构建SQL查询条件
        search_condition = ""
        params = []
        
        if request.search:
            search_condition = f"AND (t.code LIKE {PLACEHOLDER} OR t.name LIKE {PLACEHOLDER})"
            search_pattern = f'%{request.search}%'
            params.extend([search_pattern, search_pattern])
            
        # 计算总数
        count_sql = f"""
            SELECT COUNT(*) AS total
            FROM ticker t
            WHERE t.is_deleted = 0 AND t.status = 1 {search_condition}
        """
        count_result = repo.db.query_one(count_sql, tuple(params) if params else None)
        total = count_result.get('total', 0) if count_result else 0
        
        # 处理排序
        order_by_clause = "ORDER BY t.code"  # 默认排序
        
        # 支持的排序字段映射
        sort_field_mapping = {
            'code': 't.code',
            'name': 't.name',
            'score': 'ts.score',
            'update_time': 'ts.time_key'
        }
        
        if request.sort:
            sort_clauses = []
            for sort_item in request.sort:
                direction = "DESC" if sort_item.startswith('-') else "ASC"
                field_name = sort_item[1:] if sort_item.startswith('+') or sort_item.startswith('-') else sort_item
                
                # 检查字段是否在支持的排序字段列表中
                if field_name in sort_field_mapping:
                    db_field = sort_field_mapping[field_name]
                    sort_clauses.append(f"{db_field} {direction}")
            
            if sort_clauses:
                order_by_clause = f"ORDER BY {', '.join(sort_clauses)}"
        
        # 分页查询
        limit = request.page_size
        offset = (request.page - 1) * limit
        params_with_pagination = params.copy()
        params_with_pagination.extend([limit, offset])
        
        # 使用LEFT JOIN查询ticker和最新score数据
        sql = f"""
            SELECT 
                t.code, 
                t.name,
                ts.score as score,
                ts.time_key as update_time
            FROM ticker t
            LEFT JOIN ticker_score ts ON t.id = ts.ticker_id
            WHERE t.is_deleted = 0 AND t.status = 1 {search_condition}
            {order_by_clause}
            LIMIT {PLACEHOLDER} OFFSET {PLACEHOLDER}
        """
        ticker_results = repo.db.query(sql, tuple(params_with_pagination))
        
        # 处理结果
        ticker_list = []
        
        for ticker in ticker_results:
            ticker_data = {
                "code": ticker['code'],
                "name": ticker['name'],
                "score": float(ticker['score']) if ticker['score'] is not None else None
            }
            
            # 格式化日期时间
            create_time = ticker['update_time']
            if create_time:
                if isinstance(create_time, datetime):
                    ticker_data["update_time"] = int(create_time.timestamp())
                else:
                    # 尝试转换字符串为时间戳
                    try:
                        dt = datetime.fromisoformat(str(create_time).replace('Z', '+00:00'))
                        ticker_data["update_time"] = int(dt.timestamp())
                    except (ValueError, AttributeError):
                        ticker_data["update_time"] = None
            else:
                ticker_data["update_time"] = None
            
            ticker_list.append(ticker_data)
            
        return {
            "status": "success",
            "data": {
                "total": total,
                "page": request.page,
                "page_size": request.page_size,
                "list": ticker_list
            }
        }
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


@app.get("/ticker/{market}/{ticker_code}")
async def get_ticker_data(
    market: str, 
    ticker_code: str, 
    days: Optional[int] = 600
):
    """获取指定股票的详细信息和K线数据
    
    如果启用了鉴权，则只有认证用户可以访问
    """
    try:
        code = dataSource.get_ticker_code(market,ticker_code)
        ticker,kl_data,scoreData = dataSource.get_ticker_data(code,days)
       
        return {
            "status": "success", 
            "ticker": {
                "code": ticker.code,
                "name": ticker.name,
            },
            "kl_data": [{
                "time_key": kl.time_key,
                "open": float(kl.open),
                "high": float(kl.high),
                "low": float(kl.low),
                "close": float(kl.close),
                "volume": float(kl.volume)
            } for kl in kl_data],
            "scores": [{
                "time_key": scores['time_key'],
                "score": scores['score'],
            } for scores in scoreData]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cron/ticker/{market}/update")
async def cron_update_ticker_score(
    market: str, 
    background_tasks: BackgroundTasks,
    # current_user: Dict[str, Any] = Depends(auth_required(["ADMIN"])) if AUTH_ENABLED else None
):
    """
    批量更新指定市场的ticker_score，分批处理，每批100只，间隔1秒，批次间隔1分钟。
    
    需要管理员权限访问。
    """
    from core.service.ticker_repository import TickerRepository
    from core.enum.ticker_group import TickerGroup
    from core.data_source_helper import DataSourceHelper
    import math

    # 市场映射
    market_map = {
        'hk': 'HK',
        'zh': 'SZ',  # 只用SZ/SH前缀区分A股
        'us': 'US',
    }
    if market not in market_map:
        raise HTTPException(status_code=400, detail="market参数错误，只支持hk/zh/us")

    # 获取所有可用ticker
    repo = TickerRepository()
    tickers = repo.get_all_available()
    # 按市场过滤
    prefix = market_map[market]
    tickers = [t for t in tickers if t.code.startswith(prefix) or (market == 'zh' and t.code.startswith('SH'))]
    total = len(tickers)
    batch_size = 100
    batch_count = math.ceil(total / batch_size)

    def batch_update():
        ds = DataSourceHelper()
        for i in range(batch_count):
            batch = tickers[i*batch_size:(i+1)*batch_size]
            if not batch:
                continue
            ds._update_tickers(batch)
            time.sleep(60)  # 每批间隔1分钟

    background_tasks.add_task(batch_update)
    return {"status": "started", "total": total, "batch_size": batch_size, "batch_count": batch_count}

@app.middleware("http")
async def api_log_exception_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as e:
        # 记录到api_log表
        try:
            params = None
            if request.method in ("POST", "PUT", "PATCH"):
                params = (await request.body()).decode("utf-8")
            else:
                params = str(request.query_params)
            log = ApiLog(
                path=str(request.url.path),
                method=request.method,
                params=params,
                exception=str(e),
                traceback=tb.format_exc()
            )
            ApiLogRepository().insert(log)
        except Exception as log_e:
            print(f"API日志写入失败: {log_e}")
        raise