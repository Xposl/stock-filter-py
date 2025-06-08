#!/usr/bin/env python3

import logging
import os
from datetime import datetime
from typing import Any, Optional, Union

from core.database.db_adapter import DbAdapter
from core.models.market import (
    Market,
    MarketCreate,
    MarketUpdate,
    dict_to_market,
    market_to_dict,
)
from core.service.base_repository import BaseRepository

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 获取占位符类型
DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()
# SQLite 使用 ? 占位符，其他数据库使用 %s
PLACEHOLDER = "?" if DB_TYPE == "sqlite" else "%s"


class MarketRepository(BaseRepository):
    """
    使用Pydantic模型的Market仓库类（安全版本）
    """
    
    # 定义允许的表名白名单
    ALLOWED_TABLES = ["market"]

    def __init__(self, db_connection: Optional[DbAdapter] = None):
        """
        初始化Market仓库

        Args:
            db_connection: 可选的数据库连接
        """
        if db_connection:
            db = db_connection
        else:
            db = DbAdapter()
        
        # 调用父类初始化，传入安全验证的表名
        super().__init__(db, "market")

    def get_by_id(self, market_id: Union[int, str]) -> Optional[Market]:
        """
        根据ID获取市场信息

        Args:
            market_id: 市场ID

        Returns:
            Market对象或None
        """
        try:
            sql_template = "SELECT * FROM TABLE_NAME WHERE id = :id"
            result = self.safe_query_one(sql_template, {"id": market_id})
            if result:
                return dict_to_market(result)
            return None
        except Exception as e:
            logger.error(f"获取市场信息错误: {e}")
            return None

    def get_by_code(self, code: str) -> Optional[Market]:
        """
        根据市场代码获取市场信息

        Args:
            code: 市场代码

        Returns:
            Market对象或None
        """
        try:
            sql_template = "SELECT * FROM TABLE_NAME WHERE code = :code"
            result = self.safe_query_one(sql_template, {"code": code})
            if result:
                return dict_to_market(result)
            return None
        except Exception as e:
            logger.error(f"获取市场信息错误: {e}")
            return None

    def get_by_group_id(self, group_id: Union[int, str]) -> Optional[Market]:
        """
        根据group_id获取市场信息
        
        这是为了适配现有的ticker表group_id字段

        Args:
            group_id: ticker表的group_id字段值

        Returns:
            Market对象或None
        """
        return self.get_by_id(group_id)

    def get_all(self) -> list[Market]:
        """
        获取所有市场

        Returns:
            Market对象列表
        """
        try:
            sql_template = "SELECT * FROM TABLE_NAME"
            results = self.safe_query(sql_template)
            return [dict_to_market(result) for result in results]
        except Exception as e:
            logger.error(f"获取所有市场错误: {e}")
            return []

    def get_active_markets(self) -> list[Market]:
        """
        获取所有活跃市场

        Returns:
            活跃的Market对象列表
        """
        try:
            sql_template = "SELECT * FROM TABLE_NAME WHERE status = :status"
            results = self.safe_query(sql_template, {"status": 1})
            return [dict_to_market(result) for result in results]
        except Exception as e:
            logger.error(f"获取活跃市场错误: {e}")
            return []

    def create(self, market_data: Union[MarketCreate, dict]) -> Optional[Market]:
        """
        创建新市场

        Args:
            market_data: 市场数据

        Returns:
            创建的Market对象或None
        """
        try:
            if isinstance(market_data, MarketCreate):
                data_dict = market_to_dict(market_data)
            else:
                data_dict = market_data

            # 设置创建时间
            data_dict["create_time"] = datetime.now()
            
            # 构建安全的INSERT语句
            columns = list(data_dict.keys())
            placeholders = [f":{col}" for col in columns]
            
            sql_template = f"INSERT INTO TABLE_NAME ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
            self.safe_execute(sql_template, data_dict)
            
            # 返回创建的市场对象
            if "code" in data_dict:
                return self.get_by_code(data_dict["code"])
            return None
        except Exception as e:
            logger.error(f"创建市场错误: {e}")
            return None

    def update(self, market_id: Union[int, str], update_data: Union[MarketUpdate, dict]) -> Optional[Market]:
        """
        更新市场

        Args:
            market_id: 市场ID
            update_data: 更新数据

        Returns:
            更新后的Market对象或None
        """
        try:
            if isinstance(update_data, MarketUpdate):
                data_dict = market_to_dict(update_data)
            else:
                data_dict = update_data

            # 设置更新时间
            data_dict["update_time"] = datetime.now()
            data_dict["id"] = market_id

            # 构建安全的UPDATE语句
            set_clauses = [f"{col} = :{col}" for col in data_dict.keys() if col != "id"]
            sql_template = f"UPDATE TABLE_NAME SET {', '.join(set_clauses)} WHERE id = :id"
            
            self.safe_execute(sql_template, data_dict)
            return self.get_by_id(market_id)
        except Exception as e:
            logger.error(f"更新市场错误: {e}")
            return None

    def delete(self, market_id: Union[int, str]) -> bool:
        """
        删除市场（软删除）

        Args:
            market_id: 市场ID

        Returns:
            是否删除成功
        """
        try:
            sql_template = "UPDATE TABLE_NAME SET status = :status WHERE id = :id"
            self.safe_execute(sql_template, {"status": 0, "id": market_id})
            return True
        except Exception as e:
            logger.error(f"删除市场错误: {e}")
            return False

    def get_market_by_group_id(self, group_id: Union[int, str]) -> Optional[Market]:
        """
        通过group_id获取市场信息（兼容方法）
        
        这是为了适配现有的ticker表group_id字段

        Args:
            group_id: ticker表的group_id字段值

        Returns:
            Market对象或None
        """
        return self.get_by_id(group_id)

    def search_markets(self, keyword: str) -> list[Market]:
        """
        搜索市场

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的Market对象列表
        """
        try:
            sql_template = """
            SELECT * FROM TABLE_NAME 
            WHERE (code LIKE :keyword OR name LIKE :keyword OR region LIKE :keyword)
            AND status = :status
            ORDER BY code
            """
            keyword_pattern = f"%{keyword}%"
            results = self.safe_query(sql_template, {"keyword": keyword_pattern, "status": 1})
            return [dict_to_market(result) for result in results]
        except Exception as e:
            logger.error(f"搜索市场错误: {e}")
            return []
