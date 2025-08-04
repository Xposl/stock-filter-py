"""
股票估值仓储类
实现股票估值的数据访问和持久化操作
"""

import logging
from typing import List, Optional, Type, Dict, Any

from app.entities import TickerValuation, ValuationStatus
from app.entities.ticker_valuation import TickerValuationCreate, TickerValuationUpdate
from app.repositories.base_repository import BaseRepository
from app.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

class TickerValuationRepository(BaseRepository[TickerValuation, TickerValuationCreate, TickerValuationUpdate]):
    """股票估值仓储类"""
    
    def __init__(self, db_service: DatabaseService):
        super().__init__(db_service)
    
    @property
    def table_name(self) -> str:
        return "ticker_valuations"
    
    @property
    def entity_class(self) -> Type[TickerValuation]:
        return TickerValuation
    
    @property
    def create_class(self) -> Type[TickerValuationCreate]:
        return TickerValuationCreate
    
    @property
    def update_class(self) -> Type[TickerValuationUpdate]:
        return TickerValuationUpdate
    
    def get_json_fields(self) -> List[str]:
        return []  # ticker_valuations表没有JSON字段
    
    async def get_by_ticker_id_and_valuation_key(self, ticker_id: int, valuation_key: str) -> Optional[TickerValuation]:
        """根据股票ID和估值键获取估值"""
        sql = f"SELECT * FROM {self.table_name} WHERE ticker_id = :ticker_id AND valuation_key = :valuation_key"
        data = await self._execute_query_one(sql, {"ticker_id": ticker_id, "valuation_key": valuation_key})
        return self._dict_to_entity(data) if data else None
    
    async def get_by_ticker_id(self, ticker_id: int, limit: int = 100, offset: int = 0) -> List[TickerValuation]:
        """根据股票ID获取估值列表"""
        sql = f"SELECT * FROM {self.table_name} WHERE ticker_id = :ticker_id ORDER BY time_key DESC LIMIT :limit OFFSET :offset"
        rows = await self._execute_query(sql, {"ticker_id": ticker_id, "limit": limit, "offset": offset})
        return [self._dict_to_entity(row) for row in rows]
    
    async def get_by_valuation_key(self, valuation_key: str, limit: int = 100, offset: int = 0) -> List[TickerValuation]:
        """根据估值键获取估值列表"""
        sql = f"SELECT * FROM {self.table_name} WHERE valuation_key = :valuation_key ORDER BY ticker_id, time_key DESC LIMIT :limit OFFSET :offset"
        rows = await self._execute_query(sql, {"valuation_key": valuation_key, "limit": limit, "offset": offset})
        return [self._dict_to_entity(row) for row in rows]
    
    async def get_active_valuations(self, ticker_id: Optional[int] = None, limit: int = 100, offset: int = 0) -> List[TickerValuation]:
        """获取活跃估值列表"""
        where_clause = "WHERE status = :status"
        params = {"status": ValuationStatus.ACTIVE.value, "limit": limit, "offset": offset}
        
        if ticker_id:
            where_clause += " AND ticker_id = :ticker_id"
            params["ticker_id"] = ticker_id
        
        sql = f"SELECT * FROM {self.table_name} {where_clause} ORDER BY ticker_id, valuation_key, time_key DESC LIMIT :limit OFFSET :offset"
        rows = await self._execute_query(sql, params)
        return [self._dict_to_entity(row) for row in rows]
    
    async def get_valuations_by_price_range(self, min_price: float, max_price: float, limit: int = 100, offset: int = 0) -> List[TickerValuation]:
        """根据价格范围获取估值"""
        sql = f"SELECT * FROM {self.table_name} WHERE target_price BETWEEN :min_price AND :max_price ORDER BY target_price DESC LIMIT :limit OFFSET :offset"
        rows = await self._execute_query(sql, {"min_price": min_price, "max_price": max_price, "limit": limit, "offset": offset})
        return [self._dict_to_entity(row) for row in rows]
    
    async def get_valuation_statistics(self) -> Dict[str, Any]:
        """获取估值统计信息"""
        try:
            sql = """
                SELECT COUNT(*) as total_count,
                       COUNT(CASE WHEN status = 1 THEN 1 END) as active_count,
                       COUNT(DISTINCT ticker_id) as ticker_count,
                       COUNT(DISTINCT valuation_key) as valuation_type_count,
                       AVG(target_price) as avg_target_price,
                       MAX(target_price) as max_target_price,
                       MIN(target_price) as min_target_price
                FROM ticker_valuations
                WHERE target_price > 0
            """
            result = await self._execute_query_one(sql)
            return result if result else {}
        except Exception as e:
            logger.error(f"获取估值统计信息失败: {e}")
            return {}
    
    async def update_valuation_status(self, valuation_id: int, status: ValuationStatus) -> Optional[TickerValuation]:
        """更新估值状态"""
        try:
            update_data = TickerValuationUpdate(status=status.value)
            return await self.update(valuation_id, update_data)
        except Exception as e:
            logger.error(f"更新估值状态失败: {e}")
            raise 