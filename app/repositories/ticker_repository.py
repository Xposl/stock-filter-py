"""
股票仓储类
实现股票的数据访问和持久化操作
"""

import logging
from typing import List, Optional, Type, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.entities import Ticker, TickerStatus, TickerType
from app.entities.ticker import TickerCreate, TickerUpdate
from app.repositories.base_repository import BaseRepository
from app.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

class TickerRepository(BaseRepository[Ticker, TickerCreate, TickerUpdate]):
    """
    股票仓储类
    
    提供股票的数据访问和查询功能
    """
    
    def __init__(self, db_service: DatabaseService):
        super().__init__(db_service)
    
    @property
    def table_name(self) -> str:
        return "tickers"
    
    @property
    def entity_class(self) -> Type[Ticker]:
        return Ticker
    
    @property
    def create_class(self) -> Type[TickerCreate]:
        return TickerCreate
    
    @property
    def update_class(self) -> Type[TickerUpdate]:
        return TickerUpdate
    
    def get_json_fields(self) -> List[str]:
        """JSON字段列表"""
        return []  # ticker表没有JSON字段
    
    async def get_by_code(self, code: str) -> Optional[Ticker]:
        """根据股票代码获取股票"""
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE code = :code
        """
        data = await self._execute_query_one(sql, {"code": code})
        if data:
            return self._dict_to_entity(data)
        return None
    
    async def get_like_code(self, code: str) -> List[Ticker]:
        """根据股票代码模糊查询股票"""
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE code LIKE :code
            ORDER BY code
        """
        rows = await self._execute_query(sql, {"code": f"%{code}%"})
        return [self._dict_to_entity(row) for row in rows]
    
    async def get_by_type(self, ticker_type: TickerType) -> List[Ticker]:
        """根据股票类型获取股票列表"""
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE type = :type
            ORDER BY code
        """
        rows = await self._execute_query(sql, {"type": ticker_type.value})
        return [self._dict_to_entity(row) for row in rows]
    
    async def get_by_market_id(self, market_id: int) -> List[Ticker]:
        """根据市场ID获取股票列表"""
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE market_id = :market_id
            ORDER BY code
        """
        rows = await self._execute_query(sql, {"market_id": market_id})
        return [self._dict_to_entity(row) for row in rows]
    
    async def get_active_tickers(self, limit: int = 100, offset: int = 0) -> List[Ticker]:
        """获取活跃股票列表"""
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE status = :status AND is_deleted = :is_deleted
            ORDER BY code
            LIMIT :limit OFFSET :offset
        """
        if(limit == -1):
            sql = f"""
                SELECT * FROM {self.table_name}
                WHERE status = :status AND is_deleted = :is_deleted
                ORDER BY code
                OFFSET :offset
            """

        params = {
            "status": TickerStatus.ACTIVE.value,
            "is_deleted": False,
            "limit": limit,
            "offset": offset
        }
        rows = await self._execute_query(sql, params)
        return [self._dict_to_entity(row) for row in rows]
    
    async def search_tickers(
        self, 
        keyword: str, 
        ticker_type: Optional[TickerType] = None,
        market_id: Optional[int] = None,
        limit: int = 50, 
        offset: int = 0
    ) -> List[Ticker]:
        """搜索股票"""
        try:
            where_clause = "(code LIKE :keyword OR name LIKE :keyword)"
            params = {
                "keyword": f"%{keyword}%",
                "limit": limit,
                "offset": offset
            }
            
            if ticker_type:
                where_clause += " AND type = :type"
                params["type"] = ticker_type.value
            
            if market_id:
                where_clause += " AND market_id = :market_id"
                params["market_id"] = market_id
            
            sql = f"""
                SELECT * FROM {self.table_name}
                WHERE {where_clause}
                ORDER BY code
                LIMIT :limit OFFSET :offset
            """
            
            rows = await self._execute_query(sql, params)
            return [self._dict_to_entity(row) for row in rows]
            
        except Exception as e:
            logger.error(f"搜索股票失败: {e}")
            raise
    
    async def get_ticker_statistics(self) -> Dict[str, Any]:
        """获取股票统计信息"""
        try:
            sql = """
                SELECT 
                    COUNT(*) as total_count,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_count,
                    COUNT(CASE WHEN status = 'inactive' THEN 1 END) as inactive_count,
                    COUNT(CASE WHEN is_deleted = TRUE THEN 1 END) as deleted_count,
                    COUNT(CASE WHEN type = 1 THEN 1 END) as stock_count,
                    COUNT(CASE WHEN type = 2 THEN 1 END) as index_count,
                    COUNT(CASE WHEN type = 3 THEN 1 END) as bond_count,
                    COUNT(CASE WHEN type = 11 THEN 1 END) as etf_count,
                    COUNT(DISTINCT market_id) as market_count
                FROM tickers
            """
            
            result = await self._execute_query_one(sql)
            if result:
                return {
                    "total_count": result.get("total_count", 0),
                    "active_count": result.get("active_count", 0),
                    "inactive_count": result.get("inactive_count", 0),
                    "deleted_count": result.get("deleted_count", 0),
                    "stock_count": result.get("stock_count", 0),
                    "index_count": result.get("index_count", 0),
                    "bond_count": result.get("bond_count", 0),
                    "etf_count": result.get("etf_count", 0),
                    "market_count": result.get("market_count", 0)
                }
            return {}
            
        except Exception as e:
            logger.error(f"获取股票统计信息失败: {e}")
            return {}
    
    async def get_tickers_by_market_prefix(self, prefix: str) -> List[Ticker]:
        """根据市场前缀获取股票列表"""
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE code LIKE :prefix
            ORDER BY code
        """
        rows = await self._execute_query(sql, {"prefix": f"{prefix}.%"})
        return [self._dict_to_entity(row) for row in rows]
    
    async def update_ticker_status(self, ticker_id: int, status: TickerStatus) -> Optional[Ticker]:
        """更新股票状态"""
        try:
            update_data = TickerUpdate(status=status.value)
            return await self.update(ticker_id, update_data)
        except Exception as e:
            logger.error(f"更新股票状态失败: {e}")
            raise
    
    async def soft_delete_ticker(self, ticker_id: int) -> Optional[Ticker]:
        """软删除股票"""
        try:
            update_data = TickerUpdate(
                status=TickerStatus.DELETED.value,
                is_deleted=True
            )
            return await self.update(ticker_id, update_data)
        except Exception as e:
            logger.error(f"软删除股票失败: {e}")
            raise
    
    async def restore_ticker(self, ticker_id: int) -> Optional[Ticker]:
        """恢复股票"""
        try:
            update_data = TickerUpdate(
                status=TickerStatus.ACTIVE.value,
                is_deleted=False
            )
            return await self.update(ticker_id, update_data)
        except Exception as e:
            logger.error(f"恢复股票失败: {e}")
            raise
    
    async def get_tickers_with_valuation(
        self,
        limit: int = 50,
        offset: int = 0,
        min_pe: Optional[float] = None,
        max_pe: Optional[float] = None,
        min_pb: Optional[float] = None,
        max_pb: Optional[float] = None
    ) -> List[Ticker]:
        """获取带估值指标的股票列表"""
        try:
            where_conditions = []
            params = {"limit": limit, "offset": offset}
            
            if min_pe is not None:
                where_conditions.append("pe_forecast >= :min_pe")
                params["min_pe"] = min_pe
            
            if max_pe is not None:
                where_conditions.append("pe_forecast <= :max_pe")
                params["max_pe"] = max_pe
            
            if min_pb is not None:
                where_conditions.append("pb >= :min_pb")
                params["min_pb"] = min_pb
            
            if max_pb is not None:
                where_conditions.append("pb <= :max_pb")
                params["max_pb"] = max_pb
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            sql = f"""
                SELECT * FROM {self.table_name}
                WHERE {where_clause}
                ORDER BY code
                LIMIT :limit OFFSET :offset
            """
            
            rows = await self._execute_query(sql, params)
            return [self._dict_to_entity(row) for row in rows]
            
        except Exception as e:
            logger.error(f"获取带估值指标的股票列表失败: {e}")
            raise
    
    async def get_tickers_by_update_date(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Ticker]:
        """根据更新日期获取股票列表"""
        try:
            where_conditions = []
            params = {"limit": limit, "offset": offset}
            
            if start_date:
                where_conditions.append("update_date >= :start_date")
                params["start_date"] = start_date
            
            if end_date:
                where_conditions.append("update_date <= :end_date")
                params["end_date"] = end_date
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            sql = f"""
                SELECT * FROM {self.table_name}
                WHERE {where_clause}
                ORDER BY update_date DESC
                LIMIT :limit OFFSET :offset
            """
            
            rows = await self._execute_query(sql, params)
            return [self._dict_to_entity(row) for row in rows]
            
        except Exception as e:
            logger.error(f"根据更新日期获取股票列表失败: {e}")
            raise 
    
    async def get_tickers_with_market_info(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """获取带市场信息的股票列表"""
        try:
            sql = f"""
                SELECT t.*, m.name as market_name, m.code as market_code
                FROM {self.table_name} t
                LEFT JOIN markets m ON t.market_id = m.id
                ORDER BY t.code
                LIMIT :limit OFFSET :offset
            """
            
            rows = await self._execute_query(sql, {"limit": limit, "offset": offset})
            return rows
            
        except Exception as e:
            logger.error(f"获取带市场信息的股票列表失败: {e}")
            raise 