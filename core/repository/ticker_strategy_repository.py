#!/usr/bin/env python3

import logging
import os
from typing import Any, Optional

from core.database.db_adapter import DbAdapter
from core.models.ticker_strategy import TickerStrategy as TickerStrategyModel
from core.models.ticker_strategy import (
    TickerStrategyCreate,
    TickerStrategyUpdate,
    dict_to_ticker_strategy,
    ticker_strategy_to_dict,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 获取占位符类型
DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()
PLACEHOLDER = "?" if DB_TYPE == "sqlite" else "%s"


class TickerStrategyRepository:
    """
    使用Pydantic模型的TickerStrategy仓库类
    """

    table = "ticker_strategy"

    def __init__(self, db_connection: Optional[Any] = None):
        """
        初始化TickerStrategy仓库

        Args:
            db_connection: 可选的数据库连接，如果未提供将使用DbAdapter创建新连接
        """
        if db_connection:
            self.db = db_connection
        else:
            self.db = DbAdapter()

    def get_items_by_ticker_id(
        self, ticker_id: int, kl_type: str
    ) -> list[TickerStrategyModel]:
        """根据股票ID和K线类型获取所有策略记录

        Args:
            ticker_id: 股票ID
            kl_type: K线类型

        Returns:
            策略记录列表
        """
        try:
            sql = f"SELECT * FROM {self.table} WHERE ticker_id = {PLACEHOLDER} AND kl_type = {PLACEHOLDER}"
            results = self.db.query(sql, (ticker_id, kl_type))
            return [dict_to_ticker_strategy(item) for item in results]
        except Exception as e:
            logger.error(f"获取策略记录列表错误: {e}")
            return []

    def get_update_time_by_ticker_id(
        self, ticker_id: int, kl_type: str
    ) -> Optional[str]:
        """获取股票策略最早更新时间

        Args:
            ticker_id: 股票ID
            kl_type: K线类型

        Returns:
            时间字符串
        """
        try:
            sql = f"SELECT min(time_key) as time FROM {self.table} WHERE ticker_id = {PLACEHOLDER} AND kl_type = {PLACEHOLDER}"
            result = self.db.query_one(sql, (ticker_id, kl_type))
            return result["time"] if result and "time" in result else None
        except Exception as e:
            logger.error(f"获取更新时间错误: {e}")
            return None

    def get_item_by_ticker_id_and_strategy_key(
        self, ticker_id: int, strategy_key: str, kl_type: str
    ) -> Optional[TickerStrategyModel]:
        """根据股票ID, 策略键和K线类型获取策略记录

        Args:
            ticker_id: 股票ID
            strategy_key: 策略键
            kl_type: K线类型

        Returns:
            策略记录或None
        """
        try:
            sql = f"SELECT * FROM {self.table} WHERE ticker_id = {PLACEHOLDER} AND strategy_key = {PLACEHOLDER} AND kl_type = {PLACEHOLDER}"
            result = self.db.query_one(sql, (ticker_id, strategy_key, kl_type))
            return dict_to_ticker_strategy(result) if result else None
        except Exception as e:
            logger.error(f"获取策略记录错误: {e}")
            return None

    def update_item(
        self,
        ticker_id: int,
        strategy_key: str,
        kl_type: str,
        time_key: str,
        entity: dict[str, Any],
    ) -> None:
        """更新或创建策略记录

        Args:
            ticker_id: 股票ID
            strategy_key: 策略键
            kl_type: K线类型
            time_key: 时间键
            entity: 策略数据

        Returns:
            None
        """
        try:
            # 检查是否存在该记录
            existing_item = self.get_item_by_ticker_id_and_strategy_key(
                ticker_id, strategy_key, kl_type
            )

            # 准备数据
            # 确保 data 和 pos_data 是字典，如果是列表，先将其转换为字符串
            data = entity.get("data")
            pos_data = entity.get("pos_data")

            # 直接存储为序列化数据，Pydantic模型会处理JSON序列化
            entity_data = {
                "ticker_id": ticker_id,
                "strategy_key": strategy_key,
                "kl_type": kl_type,
                "time_key": time_key,
                "data": data,
                "pos_data": pos_data,
                "status": entity.get("status", 1),
            }

            if existing_item is None:
                # 创建新记录
                ticker_strategy = TickerStrategyCreate(**entity_data)
                db_data = ticker_strategy_to_dict(ticker_strategy)

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
                ticker_strategy = TickerStrategyUpdate(
                    **{
                        "time_key": time_key,
                        "data": entity.get("data"),
                        "pos_data": entity.get("pos_data"),
                        "status": entity.get("status"),
                    }
                )
                db_data = ticker_strategy_to_dict(ticker_strategy)

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
                values.extend([ticker_id, strategy_key, kl_type])

                # 构建SQL
                sql = f"UPDATE {self.table} SET {', '.join(set_clauses)} WHERE ticker_id = {PLACEHOLDER} AND strategy_key = {PLACEHOLDER} AND kl_type = {PLACEHOLDER}"

                # 执行SQL
                self.db.execute(sql, tuple(values))
                self.db.commit()

        except Exception as e:
            logger.error(f"更新策略记录错误: {e}")
            self.db.rollback()
