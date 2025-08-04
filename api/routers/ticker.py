#!/usr/bin/env python3

"""
股票Ticker相关API路由
包含股票数据查询、列表分页等功能
"""

import os
from typing import Optional

from fastapi import APIRouter, HTTPException

from core.data_source_helper import DataSourceHelper

from ..models import PageRequest

# 创建路由器 - 不设置prefix，保持原有路径结构
router = APIRouter(tags=["股票"])

# 加载环境变量
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "true").lower() == "true"

data_source = DataSourceHelper()


@router.post("/pages")
async def get_ticker_pages(request: PageRequest):
    """获取股票列表，支持分页、搜索和排序

    如果启用了鉴权，则只有认证用户可以访问
    """
    try:
        import os
        from datetime import datetime

        from core.repository.ticker_repository import TickerRepository

        # 获取ticker数据
        repo = TickerRepository()

        # 获取占位符类型
        db_type = os.getenv("DB_TYPE", "sqlite").lower()
        placeholder = "?" if db_type == "sqlite" else "%s"

        # 构建SQL查询条件
        search_condition = ""
        params = []

        if request.search:
            search_condition = (
                f"AND (t.code LIKE {placeholder} OR t.name LIKE {placeholder})"
            )
            search_pattern = f"%{request.search}%"
            params.extend([search_pattern, search_pattern])

        # 计算总数
        count_sql = f"""
            SELECT COUNT(*) AS total
            FROM ticker t
            WHERE t.is_deleted = 0 AND t.status = 1 {search_condition}
        """
        count_result = repo.db.query_one(count_sql, tuple(params) if params else ())
        total = count_result.get("total", 0) if count_result else 0

        # 处理排序
        order_by_clause = "ORDER BY t.code"  # 默认排序

        # 支持的排序字段映射
        sort_field_mapping = {
            "code": "t.code",
            "name": "t.name",
            "score": "ts.score",
            "update_time": "ts.time_key",
        }

        if request.sort:
            sort_clauses = []
            for sort_item in request.sort:
                direction = "DESC" if sort_item.startswith("-") else "ASC"
                field_name = (
                    sort_item[1:]
                    if sort_item.startswith("+") or sort_item.startswith("-")
                    else sort_item
                )

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
            LIMIT {placeholder} OFFSET {placeholder}
        """
        ticker_results = repo.db.query(sql, tuple(params_with_pagination))

        # 处理结果
        ticker_list = []

        for ticker in ticker_results:
            ticker_data = {
                "code": ticker["code"],
                "name": ticker["name"],
                "score": float(ticker["score"])
                if ticker["score"] is not None
                else None,
            }

            # 格式化日期时间
            create_time = ticker["update_time"]
            if create_time:
                if isinstance(create_time, datetime):
                    ticker_data["update_time"] = int(create_time.timestamp())
                else:
                    # 尝试转换字符串为时间戳
                    try:
                        dt = datetime.fromisoformat(
                            str(create_time).replace("Z", "+00:00")
                        )
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
                "list": ticker_list,
            },
        }
    except Exception as e:
        import traceback

        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail) from e


@router.get("/ticker/{market}/{ticker_code}")
async def get_ticker_data(market: str, ticker_code: str, days: Optional[int] = 600):
    """获取指定股票的详细信息和K线数据

    如果启用了鉴权，则只有认证用户可以访问
    """
    try:
        code = data_source.get_ticker_code(market, ticker_code)
        ticker, kl_data, score_data = data_source.get_ticker_data(code, days)

        # 检查股票是否存在
        if ticker is None:
            raise HTTPException(
                status_code=404,
                detail=f"Stock not found: {market}.{ticker_code} (code: {code})",
            )

        return {
            "status": "success",
            "ticker": {
                "code": ticker.code,
                "name": ticker.name,
            },
            "kl_data": [
                {
                    "time_key": kl.time_key,
                    "open": float(kl.open),
                    "high": float(kl.high),
                    "low": float(kl.low),
                    "close": float(kl.close),
                    "volume": float(kl.volume),
                }
                for kl in kl_data
            ]
            if kl_data
            else [],
            "scores": [
                {
                    "time_key": scores.time_key,
                    "score": scores.score,
                }
                for scores in score_data
            ]
            if score_data
            else [],
        }
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
