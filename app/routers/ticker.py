#!/usr/bin/env python3

"""
股票Ticker相关API路由
包含股票数据查询、列表分页等功能
"""

import os
import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.utils.response_utils import (
    PaginatedData, SuccessResponse, create_success_response, create_error_response, create_paginated_response
)
from app.auth.auth_middleware import get_current_user, get_current_user_id

logger = logging.getLogger(__name__)

# 创建路由器 - 设置统一的API前缀
router = APIRouter(
    prefix="/api/v1/ticker",
    tags=["股票数据"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)

# ================== Request/Response Models ==================

class TickerPageRequest(BaseModel):
    """股票分页请求"""
    page: int = Field(1, description="页码", ge=1)
    page_size: int = Field(50, description="每页数量", ge=1, le=100)
    search: Optional[str] = Field(None, description="搜索关键词")
    sort: Optional[list] = Field(None, description="排序字段列表")

class TickerDataResponse(BaseModel):
    """股票数据响应"""
    code: str
    name: str
    score: Optional[float] = None
    update_time: Optional[int] = None

class TickerDetailResponse(BaseModel):
    """股票详情响应"""
    code: str
    name: str
    kl_data: list
    scores: list

# ================== Health Check ==================

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    股票服务健康检查
    """
    try:
        health_data = {
            "status": "healthy",
            "service": "ticker",
            "data_source": "available"
        }

        return create_success_response(
            data=health_data,
            message="股票服务健康"
        )

    except Exception as e:
        logger.error(f"股票服务健康检查失败: {e}")
        return create_error_response(
            message="股票服务异常",
            details=str(e),
            error_type="HealthCheckError",
            code=503
        )

# ================== Ticker Endpoints ==================

@router.post("/pages", response_model=SuccessResponse[PaginatedData[TickerDataResponse]])
async def get_ticker_pages(
    request: TickerPageRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """获取股票列表，支持分页、搜索和排序"""
    # try:
    #     import os
    #     from datetime import datetime

    #     from core.repository.ticker_repository import TickerRepository

    #     user_id = str(current_user.get("user_id", "anonymous"))
    #     logger.info(f"获取股票列表: user={user_id}, page={request.page}, search={request.search}")

    #     # 获取ticker数据
    #     repo = TickerRepository()

    #     # 获取占位符类型
    #     db_type = os.getenv("DB_TYPE", "sqlite").lower()
    #     placeholder = "?" if db_type == "sqlite" else "%s"

    #     # 构建SQL查询条件
    #     search_condition = ""
    #     params = []

    #     if request.search:
    #         search_condition = (
    #             f"AND (t.code LIKE {placeholder} OR t.name LIKE {placeholder})"
    #         )
    #         search_pattern = f"%{request.search}%"
    #         params.extend([search_pattern, search_pattern])

    #     # 计算总数
    #     count_sql = f"""
    #         SELECT COUNT(*) AS total
    #         FROM ticker t
    #         WHERE t.is_deleted = 0 AND t.status = 1 {search_condition}
    #     """
    #     count_result = repo.db.query_one(count_sql, tuple(params) if params else ())
    #     total = count_result.get("total", 0) if count_result else 0

    #     # 处理排序
    #     order_by_clause = "ORDER BY t.code"  # 默认排序

    #     # 支持的排序字段映射
    #     sort_field_mapping = {
    #         "code": "t.code",
    #         "name": "t.name",
    #         "score": "ts.score",
    #         "update_time": "ts.time_key",
    #     }

    #     if request.sort:
    #         sort_clauses = []
    #         for sort_item in request.sort:
    #             direction = "DESC" if sort_item.startswith("-") else "ASC"
    #             field_name = (
    #                 sort_item[1:]
    #                 if sort_item.startswith("+") or sort_item.startswith("-")
    #                 else sort_item
    #             )

    #             # 检查字段是否在支持的排序字段列表中
    #             if field_name in sort_field_mapping:
    #                 db_field = sort_field_mapping[field_name]
    #                 sort_clauses.append(f"{db_field} {direction}")

    #         if sort_clauses:
    #             order_by_clause = f"ORDER BY {', '.join(sort_clauses)}"

    #     # 分页查询
    #     limit = request.page_size
    #     offset = (request.page - 1) * limit
    #     params_with_pagination = params.copy()
    #     params_with_pagination.extend([limit, offset])

    #     # 使用LEFT JOIN查询ticker和最新score数据
    #     sql = f"""
    #         SELECT
    #             t.code,
    #             t.name,
    #             ts.score as score,
    #             ts.time_key as update_time
    #         FROM ticker t
    #         LEFT JOIN ticker_score ts ON t.id = ts.ticker_id
    #         WHERE t.is_deleted = 0 AND t.status = 1 {search_condition}
    #         {order_by_clause}
    #         LIMIT {placeholder} OFFSET {placeholder}
    #     """
    #     ticker_results = repo.db.query(sql, tuple(params_with_pagination))

    #     # 处理结果
    #     ticker_list = []

    #     for ticker in ticker_results:
    #         ticker_data = {
    #             "code": ticker["code"],
    #             "name": ticker["name"],
    #             "score": float(ticker["score"])
    #             if ticker["score"] is not None
    #             else None,
    #         }

    #         # 格式化日期时间
    #         create_time = ticker["update_time"]
    #         if create_time:
    #             if isinstance(create_time, datetime):
    #                 ticker_data["update_time"] = int(create_time.timestamp())
    #             else:
    #                 # 尝试转换字符串为时间戳
    #                 try:
    #                     dt = datetime.fromisoformat(
    #                         str(create_time).replace("Z", "+00:00")
    #                     )
    #                     ticker_data["update_time"] = int(dt.timestamp())
    #                 except (ValueError, AttributeError):
    #                     ticker_data["update_time"] = None
    #         else:
    #             ticker_data["update_time"] = None

    #         ticker_list.append(ticker_data)

    #     # 使用统一的响应格式
    #     return create_paginated_response(
    #         items=ticker_list,
    #         total=total,
    #         page=request.page,
    #         page_size=request.page_size,
    #         message="获取股票列表成功"
    #     )

    # except Exception as e:
    #     logger.error(f"获取股票列表失败: {e}")
    #     raise HTTPException(
    #         status_code=500,
    #         detail=create_error_response(
    #             message="获取股票列表失败",
    #             details=str(e),
    #             error_type="InternalError",
    #             code=500
    #         )
    #     )
    return None

@router.get("/{market}/{ticker_code}", response_model=SuccessResponse[TickerDetailResponse])
async def get_ticker_data(
    market: str, 
    ticker_code: str, 
    days: Optional[int] = Query(600, description="K线数据天数", ge=1, le=1000),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """获取指定股票的详细信息和K线数据"""
    # try:
    #     user_id = str(current_user.get("user_id", "anonymous"))
    #     logger.info(f"获取股票数据: user={user_id}, market={market}, ticker={ticker_code}, days={days}")

    #     code = data_source.get_ticker_code(market, ticker_code)
    #     ticker, kl_data, score_data = data_source.get_ticker_data(code, days)

    #     # 检查股票是否存在
    #     if ticker is None:
    #         logger.warning(f"股票不存在: {market}.{ticker_code} (code: {code})")
    #         raise HTTPException(
    #             status_code=404,
    #             detail=create_error_response(
    #                 message=f"股票不存在: {market}.{ticker_code}",
    #                 error_type="NotFoundError",
    #                 code=404
    #             )
    #         )

    #     # 构建响应数据
    #     response_data = {
    #         "code": ticker.code,
    #         "name": ticker.name,
    #         "kl_data": [
    #             {
    #                 "time_key": kl.time_key,
    #                 "open": float(kl.open),
    #                 "high": float(kl.high),
    #                 "low": float(kl.low),
    #                 "close": float(kl.close),
    #                 "volume": float(kl.volume),
    #             }
    #             for kl in kl_data
    #         ]
    #         if kl_data
    #         else [],
    #         "scores": [
    #             {
    #                 "time_key": scores.time_key,
    #                 "score": scores.score,
    #             }
    #             for scores in score_data
    #         ]
    #         if score_data
    #         else [],
    #     }

    #     return create_success_response(
    #         data=response_data,
    #         message="获取股票数据成功"
    #     )

    # except HTTPException:
    #     # 重新抛出HTTP异常
    #     raise
    # except Exception as e:
    #     logger.error(f"获取股票数据失败: {e}")
    #     raise HTTPException(
    #         status_code=500,
    #         detail=create_error_response(
    #             message="获取股票数据失败",
    #             details=str(e),
    #             error_type="InternalError",
    #             code=500
    #         )
    #     )
    return None
