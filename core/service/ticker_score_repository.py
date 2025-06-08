#!/usr/bin/env python3

import logging
import os
from typing import Any, Optional

from core.database.db_adapter import DbAdapter
from core.models.ticker_score import TickerScore as TickerScoreModel
from core.models.ticker_score import (
    TickerScoreCreate,
    dict_to_ticker_score,
    ticker_score_to_dict,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 获取占位符类型
DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()
PLACEHOLDER = "?" if DB_TYPE == "sqlite" else "%s"


class TickerScoreRepository:
    """
    使用Pydantic模型的TickerScore仓库类
    """

    table = "ticker_score"

    def __init__(self, db_connection: Optional[Any] = None):
        """
        初始化TickerScore仓库

        Args:
            db_connection: 可选的数据库连接，如果未提供将使用DbAdapter创建新连接
        """
        if db_connection:
            self.db = db_connection
        else:
            self.db = DbAdapter()

    def get_items_by_ticker_id(self, ticker_id: int) -> list[TickerScoreModel]:
        """根据股票ID获取所有评分记录

        Args:
            ticker_id: 股票ID

        Returns:
            评分记录列表
        """
        try:
            sql = f"SELECT * FROM {self.table} WHERE ticker_id = {PLACEHOLDER} ORDER BY time_key DESC"
            results = self.db.query(sql, (ticker_id,))
            return [dict_to_ticker_score(item) for item in results]
        except Exception as e:
            logger.error(f"获取评分记录列表错误: {e}")
            return []

    def clear_items_by_ticker_id(self, ticker_id: int) -> None:
        """清除股票的所有评分记录

        Args:
            ticker_id: 股票ID

        Returns:
            None
        """
        try:
            sql = f"DELETE FROM {self.table} WHERE ticker_id = {PLACEHOLDER}"
            self.db.execute(sql, (ticker_id,))
            self.db.commit()
        except Exception as e:
            logger.error(f"清除评分记录错误: {e}")
            self.db.rollback()

    def insert_item(self, item: dict[str, Any]) -> Optional[int]:
        """插入单条评分记录

        Args:
            item: 评分数据字典

        Returns:
            插入记录的ID或None
        """
        try:
            # 🔥 修复history字段的JSON反序列化问题
            item_data = item.copy()
            if "history" in item_data and isinstance(item_data["history"], str):
                try:
                    import json

                    item_data["history"] = json.loads(item_data["history"])
                except (ValueError, json.JSONDecodeError):
                    item_data["history"] = None

            # 创建模型实例
            score = TickerScoreCreate(**item_data)
            db_data = ticker_score_to_dict(score)

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

            # 返回最后插入的ID
            return self.db.last_insert_id()
        except Exception as e:
            logger.error(f"插入评分记录错误: {e}")
            self.db.rollback()
            return None

    def update_items(self, ticker_id: int, items: list[dict[str, Any]]) -> None:
        """批量更新评分记录（先删除旧记录，再插入新记录）

        Args:
            ticker_id: 股票ID
            items: 评分数据列表

        Returns:
            None
        """
        if not items:
            return

        try:
            # 先清除旧记录
            self.clear_items_by_ticker_id(ticker_id)

            # 准备批量插入数据
            insert_items = []

            for index, item in enumerate(items):
                # 生成ID (类似于原始实现)
                id = ticker_id * 1000 + index

                # 确保数据包含必要字段
                item_data = item.copy()
                item_data["id"] = id
                item_data["ticker_id"] = ticker_id

                # 🔥 修复history字段的JSON反序列化问题
                if "history" in item_data and isinstance(item_data["history"], str):
                    try:
                        import json

                        item_data["history"] = json.loads(item_data["history"])
                    except (ValueError, json.JSONDecodeError):
                        item_data["history"] = None

                insert_items.append(item_data)

            if not insert_items:
                return

            # 批量插入数据
            # 获取第一条数据的所有字段来构建SQL
            first_item = TickerScoreCreate(**insert_items[0])
            first_dict = ticker_score_to_dict(first_item)

            fields = list(first_dict.keys())
            placeholders = ", ".join([PLACEHOLDER] * len(fields))
            field_str = ", ".join(fields)

            # 构建批量插入VALUES部分
            values_list = []
            all_values = []

            for item_data in insert_items:
                # 🔥 再次确保history字段正确处理
                if "history" in item_data and isinstance(item_data["history"], str):
                    try:
                        import json

                        item_data["history"] = json.loads(item_data["history"])
                    except (ValueError, json.JSONDecodeError):
                        item_data["history"] = None

                score = TickerScoreCreate(**item_data)
                data_dict = ticker_score_to_dict(score)

                # 确保字段顺序一致
                item_values = []
                for field in fields:
                    item_values.append(data_dict.get(field))

                all_values.extend(item_values)
                values_list.append(f"({placeholders})")

            # 构建最终SQL
            sql = f"INSERT INTO {self.table} ({field_str}) VALUES {', '.join(values_list)}"

            # 执行SQL
            self.db.execute(sql, tuple(all_values))
            self.db.commit()

        except Exception as e:
            logger.error(f"批量更新评分记录错误: {e}")
            self.db.rollback()
