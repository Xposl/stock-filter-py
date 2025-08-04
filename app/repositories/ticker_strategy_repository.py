"""
股票策略仓储类
实现股票策略的数据访问和持久化操作
"""

import logging
from typing import List, Optional, Type, Dict, Any

from app.entities import TickerStrategy, StrategyStatus
from app.entities.ticker_strategy import TickerStrategyCreate, TickerStrategyUpdate
from app.repositories.base_repository import BaseRepository
from app.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

class TickerStrategyRepository(BaseRepository[TickerStrategy, TickerStrategyCreate, TickerStrategyUpdate]):
    """股票策略仓储类"""
    
    def __init__(self, db_service: DatabaseService):
        super().__init__(db_service)
    
    @property
    def table_name(self) -> str:
        return "ticker_strategies"
    
    @property
    def entity_class(self) -> Type[TickerStrategy]:
        return TickerStrategy
    
    @property
    def create_class(self) -> Type[TickerStrategyCreate]:
        return TickerStrategyCreate
    
    @property
    def update_class(self) -> Type[TickerStrategyUpdate]:
        return TickerStrategyUpdate
    
    def get_json_fields(self) -> List[str]:
        return ["data", "pos_data"]
    
    async def get_by_ticker_id_and_strategy_key(self, ticker_id: int, strategy_key: str, kl_type: str) -> Optional[TickerStrategy]:
        """根据股票ID、策略键和K线类型获取策略"""
        sql = f"SELECT * FROM {self.table_name} WHERE ticker_id = :ticker_id AND strategy_key = :strategy_key AND kl_type = :kl_type"
        data = await self._execute_query_one(sql, {"ticker_id": ticker_id, "strategy_key": strategy_key, "kl_type": kl_type})
        return self._dict_to_entity(data) if data else None
    
    async def get_by_ticker_id_and_kl_type(self, ticker_id: int, kl_type: str) -> List[TickerStrategy]:
        """根据股票ID和K线类型获取所有策略"""
        sql = f"SELECT * FROM {self.table_name} WHERE ticker_id = :ticker_id AND kl_type = :kl_type ORDER BY strategy_key"
        rows = await self._execute_query(sql, {"ticker_id": ticker_id, "kl_type": kl_type})
        return [self._dict_to_entity(row) for row in rows]
    
    async def get_by_strategy_key(self, strategy_key: str, limit: int = 100, offset: int = 0) -> List[TickerStrategy]:
        """根据策略键获取策略列表"""
        sql = f"SELECT * FROM {self.table_name} WHERE strategy_key = :strategy_key ORDER BY ticker_id, kl_type LIMIT :limit OFFSET :offset"
        rows = await self._execute_query(sql, {"strategy_key": strategy_key, "limit": limit, "offset": offset})
        return [self._dict_to_entity(row) for row in rows]
    
    async def get_active_strategies(self, ticker_id: Optional[int] = None, limit: int = 100, offset: int = 0) -> List[TickerStrategy]:
        """获取活跃策略列表"""
        where_clause = "WHERE status = :status"
        params = {"status": StrategyStatus.ACTIVE.value, "limit": limit, "offset": offset}
        
        if ticker_id:
            where_clause += " AND ticker_id = :ticker_id"
            params["ticker_id"] = ticker_id
        
        sql = f"SELECT * FROM {self.table_name} {where_clause} ORDER BY ticker_id, strategy_key, kl_type LIMIT :limit OFFSET :offset"
        rows = await self._execute_query(sql, params)
        return [self._dict_to_entity(row) for row in rows]
    
    async def get_strategies_with_positions(self, limit: int = 50, offset: int = 0) -> List[TickerStrategy]:
        """获取有持仓的策略列表"""
        sql = f"SELECT * FROM {self.table_name} WHERE pos_data IS NOT NULL AND JSON_LENGTH(pos_data) > 0 ORDER BY ticker_id, strategy_key LIMIT :limit OFFSET :offset"
        rows = await self._execute_query(sql, {"limit": limit, "offset": offset})
        return [self._dict_to_entity(row) for row in rows]
    
    async def get_strategy_statistics(self) -> Dict[str, Any]:
        """获取策略统计信息"""
        try:
            sql = """
                SELECT COUNT(*) as total_count,
                       COUNT(CASE WHEN status = 1 THEN 1 END) as active_count,
                       COUNT(DISTINCT ticker_id) as ticker_count,
                       COUNT(DISTINCT strategy_key) as strategy_type_count,
                       COUNT(DISTINCT kl_type) as kl_type_count
                FROM ticker_strategies
            """
            result = await self._execute_query_one(sql)
            return result if result else {}
        except Exception as e:
            logger.error(f"获取策略统计信息失败: {e}")
            return {}
    
    async def update_strategy_status(self, strategy_id: int, status: StrategyStatus) -> Optional[TickerStrategy]:
        """更新策略状态"""
        try:
            update_data = TickerStrategyUpdate(status=status.value)
            return await self.update(strategy_id, update_data)
        except Exception as e:
            logger.error(f"更新策略状态失败: {e}")
            raise 