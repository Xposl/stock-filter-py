#!/usr/bin/env python3

import logging
import os
from datetime import datetime
from typing import Any, Optional, Union, List

from core.database.db_adapter import DbAdapter
from core.models.market import (
    Market,
    MarketCreate,
    MarketUpdate,
    dict_to_market,
    market_to_dict,
)
from core.repository.base_repository import BaseRepository

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
    使用Pydantic模型的Market仓库类
    """
    
    # 定义允许的表名白名单
    ALLOWED_TABLES = ["market"]
    
    table = "market"

    def __init__(self, db_connection: Optional[Any] = None):
        """
        初始化Market仓库

        Args:
            db_connection: 可选的数据库连接，如果未提供将使用DbAdapter创建新连接
        """
        if db_connection:
            self.db = db_connection
        else:
            self.db = DbAdapter()
        
        # 调用父类初始化
        from app.services.database_service import get_database_service
        db_service = get_database_service()
        super().__init__(db_service)

    @property
    def table_name(self) -> str:
        """表名"""
        return "market"
    
    @property
    def entity_class(self):
        """实体类"""
        return Market
    
    @property
    def create_class(self):
        """创建模型类"""
        return MarketCreate
    
    @property
    def update_class(self):
        """更新模型类"""
        return MarketUpdate
    
    def get_json_fields(self) -> List[str]:
        """获取JSON字段列表"""
        return []  # Market模型没有JSON字段
        """
        初始化Market仓库

        Args:
            db_connection: 可选的数据库连接，如果未提供将使用DbAdapter创建新连接
        """
        if db_connection:
            self.db = db_connection
        else:
            self.db = DbAdapter()

    def get_by_id(self, market_id: int) -> Optional[Market]:
        """
        根据ID获取市场信息

        Args:
            market_id: 市场ID

        Returns:
            Market对象或None
        """
        try:
            sql = f"SELECT * FROM {self.table} WHERE id = :id"
            result = self.db.query_one(sql, {"id": market_id})
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
            sql = f"SELECT * FROM {self.table} WHERE code = :code"
            result = self.db.query_one(sql, {"code": code})
            if result:
                return dict_to_market(result)
            return None
        except Exception as e:
            logger.error(f"获取市场信息错误: {e}")
            return None

    def get_by_group_id(self, group_id: int) -> Optional[Market]:
        """
        根据group_id获取市场信息（适配ticker.group_id字段）

        Args:
            group_id: 组ID（对应market.id）

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
            sql = f"SELECT * FROM {self.table} ORDER BY id"
            results = self.db.query_all(sql)
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
            sql = f"SELECT * FROM {self.table} WHERE status = :status ORDER BY id"
            results = self.db.query_all(sql, {"status": 1})
            return [dict_to_market(result) for result in results]
        except Exception as e:
            logger.error(f"获取活跃市场错误: {e}")
            return []

    def create(
        self, market_data: Union[MarketCreate, dict[str, Any]]
    ) -> Optional[Market]:
        """
        创建新市场

        Args:
            market_data: 市场数据

        Returns:
            创建的Market对象或None
        """
        try:
            # 转换为字典
            if isinstance(market_data, MarketCreate):
                data_dict = market_to_dict(market_data)
            else:
                data_dict = market_data.copy()

            # 检查市场代码是否已存在
            existing = self.get_by_code(data_dict.get("code", ""))
            if existing:
                logger.warning(f"市场代码已存在: {data_dict.get('code')}")
                return None

            # 构建插入SQL
            columns = list(data_dict.keys())
            placeholders = [f":{col}" for col in columns]

            sql = f"""
            INSERT INTO {self.table} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            """

            # 执行插入
            market_id = self.db.execute_and_fetch_id(sql, data_dict)

            if market_id:
                logger.info(f"成功创建市场: {data_dict.get('name')} (ID: {market_id})")
                return self.get_by_id(market_id)
            return None

        except Exception as e:
            logger.error(f"创建市场失败: {e}")
            return None

    def update(
        self, market_id: int, update_data: Union[MarketUpdate, dict[str, Any]]
    ) -> Optional[Market]:
        """
        更新市场信息

        Args:
            market_id: 市场ID
            update_data: 更新数据

        Returns:
            更新后的Market对象或None
        """
        try:
            # 转换为字典
            if isinstance(update_data, MarketUpdate):
                data_dict = market_to_dict(update_data)
            else:
                data_dict = update_data.copy()

            if not data_dict:
                logger.warning("没有更新数据")
                return self.get_by_id(market_id)

            # 添加更新时间
            data_dict["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 构建更新SQL
            set_clauses = [f"{col} = :{col}" for col in data_dict.keys()]
            data_dict["market_id"] = market_id

            sql = f"""
            UPDATE {self.table}
            SET {', '.join(set_clauses)}
            WHERE id = :market_id
            """

            # 执行更新
            affected_rows = self.db.execute(sql, data_dict)

            if affected_rows > 0:
                logger.info(f"成功更新市场: ID {market_id}")
                return self.get_by_id(market_id)
            return None

        except Exception as e:
            logger.error(f"更新市场失败: {e}")
            return None

    def delete(self, market_id: int) -> bool:
        """
        删除市场（软删除，设置status=0）

        Args:
            market_id: 市场ID

        Returns:
            是否删除成功
        """
        try:
            sql = f"UPDATE {self.table} SET status = :status WHERE id = :id"
            affected_rows = self.db.execute(sql, {"status": 0, "id": market_id})

            if affected_rows > 0:
                logger.info(f"成功删除市场: ID {market_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"删除市场失败: {e}")
            return False

    def get_market_by_ticker_group(self, group_id: int) -> Optional[Market]:
        """
        根据ticker的group_id获取对应的市场信息
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
            sql = f"""
            SELECT * FROM {self.table}
            WHERE (code LIKE :keyword OR name LIKE :keyword OR region LIKE :keyword)
            AND status = :status
            ORDER BY id
            """
            keyword_pattern = f"%{keyword}%"
            results = self.db.query_all(sql, {"keyword": keyword_pattern, "status": 1})
            return [dict_to_market(result) for result in results]
        except Exception as e:
            logger.error(f"搜索市场错误: {e}")
            return []
