#!/usr/bin/env python3

import logging
import os
from typing import Any, Optional

from core.database.db_adapter import DbAdapter
from core.models.ticker_valuation import TickerValuation as TickerValuationModel
from core.models.ticker_valuation import (
    TickerValuationCreate,
    TickerValuationUpdate,
    dict_to_ticker_valuation,
    ticker_valuation_to_dict,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 获取占位符类型
DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()
PLACEHOLDER = "?" if DB_TYPE == "sqlite" else "%s"


class TickerValuationRepository:
    """
    使用Pydantic模型的TickerValuation仓库类
    """

    table = "ticker_valuation"

    def __init__(self, db_connection: Optional[Any] = None):
        """
        初始化TickerValuation仓库

        Args:
            db_connection: 可选的数据库连接，如果未提供将使用DbAdapter创建新连接
        """
        if db_connection:
            self.db = db_connection
        else:
            self.db = DbAdapter()

    def get_items_by_ticker_id(self, ticker_id: int) -> list[TickerValuationModel]:
        """根据股票ID获取所有估值记录

        Args:
            ticker_id: 股票ID

        Returns:
            估值记录列表
        """
        try:
            sql = f"SELECT * FROM {self.table} WHERE ticker_id = {PLACEHOLDER}"
            results = self.db.query(sql, (ticker_id,))
            return [dict_to_ticker_valuation(item) for item in results]
        except Exception as e:
            logger.error(f"获取估值记录列表错误: {e}")
            return []

    def get_update_time_by_ticker_id(self, ticker_id: int) -> Optional[str]:
        """获取股票估值最早更新时间

        Args:
            ticker_id: 股票ID

        Returns:
            时间字符串
        """
        try:
            sql = f"SELECT min(time_key) as time FROM {self.table} WHERE ticker_id = {PLACEHOLDER}"
            result = self.db.query_one(sql, (ticker_id,))
            return result["time"] if result and "time" in result else None
        except Exception as e:
            logger.error(f"获取更新时间错误: {e}")
            return None

    def get_item_by_ticker_id_and_key(
        self, ticker_id: int, valuation_key: str
    ) -> Optional[TickerValuationModel]:
        """根据股票ID和估值键获取估值记录

        Args:
            ticker_id: 股票ID
            valuation_key: 估值键

        Returns:
            估值记录或None
        """
        try:
            sql = f"SELECT * FROM {self.table} WHERE ticker_id = {PLACEHOLDER} AND valuation_key = {PLACEHOLDER}"
            result = self.db.query_one(sql, (ticker_id, valuation_key))
            return dict_to_ticker_valuation(result) if result else None
        except Exception as e:
            logger.error(f"获取估值记录错误: {e}")
            return None

    def update_item(
        self, ticker_id: int, valuation_key: str, time_key: str, entity: dict[str, Any]
    ) -> None:
        """更新或创建估值记录

        Args:
            ticker_id: 股票ID
            valuation_key: 估值键
            time_key: 时间键
            entity: 估值数据

        Returns:
            None
        """
        try:
            # 检查是否存在该记录
            existing_item = self.get_item_by_ticker_id_and_key(ticker_id, valuation_key)

            # 准备数据
            entity_data = {
                "ticker_id": ticker_id,
                "valuation_key": valuation_key,
                "time_key": time_key,
                "target_price": entity.get("target_price", -1),
                "max_target_price": entity.get("max_target_price", -1),
                "min_target_price": entity.get("min_target_price", -1),
                "remark": entity.get("remark"),
                "status": entity.get("status", 1),
            }

            if existing_item is None:
                # 创建新记录
                ticker_valuation = TickerValuationCreate(**entity_data)
                db_data = ticker_valuation_to_dict(ticker_valuation)

                # 构建SQL参数和占位符
                fields = []
                placeholders = []
                values = []

                for key, value in db_data.items():
                    fields.append(key)
                    placeholders.append(PLACEHOLDER)
                    values.append(value)

                # 构建SQL
                sql = f"INSERT INTO {self.table} ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"

                # 执行SQL
                self.db.execute(sql, tuple(values))
                self.db.commit()
            else:
                # 更新现有记录
                ticker_valuation = TickerValuationUpdate(
                    **{
                        "time_key": time_key,
                        "target_price": entity.get("target_price"),
                        "max_target_price": entity.get("max_target_price"),
                        "min_target_price": entity.get("min_target_price"),
                        "remark": entity.get("remark"),
                        "status": entity.get("status"),
                    }
                )
                db_data = ticker_valuation_to_dict(ticker_valuation)

                # 排除不更新的字段
                exclude_keys = [
                    "id",
                    "code",
                    "version",
                    "create_time",
                    "creator",
                    "mender",
                ]
                for key in exclude_keys:
                    if key in db_data:
                        del db_data[key]

                # 过滤None值
                filtered_data = {k: v for k, v in db_data.items() if v is not None}

                if not filtered_data:
                    return

                # 构建SQL参数和SET子句
                set_clauses = []
                values = []

                for key, value in filtered_data.items():
                    set_clauses.append(f"{key} = {PLACEHOLDER}")
                    values.append(value)

                # 添加条件参数
                values.extend([ticker_id, valuation_key])

                # 构建SQL
                sql = f"UPDATE {self.table} SET {', '.join(set_clauses)} WHERE ticker_id = {PLACEHOLDER} AND valuation_key = {PLACEHOLDER}"

                # 执行SQL
                self.db.execute(sql, tuple(values))
                self.db.commit()

        except Exception as e:
            logger.error(f"更新估值记录错误: {e}")
            self.db.rollback()
