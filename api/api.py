from fastapi import FastAPI, HTTPException, Depends
from typing import Dict, Any
from core.auth.auth_middleware import auth_required
import os
from fastapi.requests import Request
from core.service.api_log_repository import ApiLogRepository
from core.models.api_log import ApiLog
import traceback as tb

# 导入路由模块
from .routers import ticker, news, scheduler

app = FastAPI(
    title="InvestNote API",
    description="Investment notes and analysis API",
    root_path="/investnote",  # 添加根路径前缀
    docs_url="/docs",  # Swagger文档路径
    redoc_url="/redoc",  # ReDoc文档路径
)

# 加载环境变量
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "true").lower() == "true"

# 注册路由模块
app.include_router(ticker.router)
app.include_router(news.router)
app.include_router(scheduler.router)

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