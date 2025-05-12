from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from core.data_source_helper import DataSourceHelper
from .models import PageRequest

app = FastAPI(
    title="InvestNote API",
    description="Investment notes and analysis API",
    root_path="/investnote"  # 添加根路径前缀
)
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

@app.post("/pages")
async def get_ticker_pages(request: PageRequest):
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
            ORDER BY t.code
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
async def get_ticker_data(market: str, ticker_code: str, days: Optional[int] = 600):
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