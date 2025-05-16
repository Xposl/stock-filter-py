from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from core.data_source_helper import DataSourceHelper
from .models import PageRequest
from core.auth.auth_middleware import auth_required
import time
import os

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

@app.post("/pages")
async def get_ticker_pages(
    request: PageRequest,
    current_user: Optional[Dict[str, Any]] = Depends(auth_required()) if AUTH_ENABLED else None
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
    days: Optional[int] = 600,
    current_user: Optional[Dict[str, Any]] = Depends(auth_required()) if AUTH_ENABLED else None
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
    current_user: Dict[str, Any] = Depends(auth_required(["ADMIN"])) if AUTH_ENABLED else None
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