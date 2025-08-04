"""
股票评分仓储类
实现股票评分的数据访问和持久化操作
"""

import logging
from typing import List, Optional, Type, Dict, Any

from app.entities import TickerScore, ScoreStatus
from app.entities.ticker_score import TickerScoreCreate, TickerScoreUpdate
from app.repositories.base_repository import BaseRepository
from app.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

class TickerScoreRepository(BaseRepository[TickerScore, TickerScoreCreate, TickerScoreUpdate]):
    """股票评分仓储类"""
    
    def __init__(self, db_service: DatabaseService):
        super().__init__(db_service)
    
    @property
    def table_name(self) -> str:
        return "ticker_scores"
    
    @property
    def entity_class(self) -> Type[TickerScore]:
        return TickerScore
    
    @property
    def create_class(self) -> Type[TickerScoreCreate]:
        return TickerScoreCreate
    
    @property
    def update_class(self) -> Type[TickerScoreUpdate]:
        return TickerScoreUpdate
    
    def get_json_fields(self) -> List[str]:
        return ["history", "analysis_data"]
    
    async def get_by_ticker_id_and_time_key(self, ticker_id: int, time_key: str) -> Optional[TickerScore]:
        """根据股票ID和时间键获取评分"""
        sql = f"SELECT * FROM {self.table_name} WHERE ticker_id = :ticker_id AND time_key = :time_key"
        data = await self._execute_query_one(sql, {"ticker_id": ticker_id, "time_key": time_key})
        return self._dict_to_entity(data) if data else None
    
    async def get_by_ticker_id(self, ticker_id: int, limit: int = 100, offset: int = 0) -> List[TickerScore]:
        """根据股票ID获取评分列表"""
        sql = f"SELECT * FROM {self.table_name} WHERE ticker_id = :ticker_id ORDER BY time_key DESC LIMIT :limit OFFSET :offset"
        rows = await self._execute_query(sql, {"ticker_id": ticker_id, "limit": limit, "offset": offset})
        return [self._dict_to_entity(row) for row in rows]
    
    async def get_latest_score_by_ticker(self, ticker_id: int) -> Optional[TickerScore]:
        """获取股票最新评分"""
        sql = f"SELECT * FROM {self.table_name} WHERE ticker_id = :ticker_id ORDER BY time_key DESC LIMIT 1"
        data = await self._execute_query_one(sql, {"ticker_id": ticker_id})
        return self._dict_to_entity(data) if data else None
    
    async def get_active_scores(self, ticker_id: Optional[int] = None, limit: int = 100, offset: int = 0) -> List[TickerScore]:
        """获取活跃评分列表"""
        where_clause = "WHERE status = :status"
        params = {"status": ScoreStatus.ACTIVE.value, "limit": limit, "offset": offset}
        
        if ticker_id:
            where_clause += " AND ticker_id = :ticker_id"
            params["ticker_id"] = ticker_id
        
        sql = f"SELECT * FROM {self.table_name} {where_clause} ORDER BY time_key DESC LIMIT :limit OFFSET :offset"
        rows = await self._execute_query(sql, params)
        return [self._dict_to_entity(row) for row in rows]
    
    async def get_score_statistics(self) -> Dict[str, Any]:
        """获取评分统计信息"""
        try:
            sql = """
                SELECT COUNT(*) as total_count,
                       COUNT(CASE WHEN status = 1 THEN 1 END) as active_count,
                       AVG(score) as avg_score,
                       MAX(score) as max_score,
                       MIN(score) as min_score
                FROM ticker_scores
            """
            result = await self._execute_query_one(sql)
            return result if result else {}
        except Exception as e:
            logger.error(f"获取评分统计信息失败: {e}")
            return {}
    
    async def update_score_status(self, score_id: int, status: ScoreStatus) -> Optional[TickerScore]:
        """更新评分状态"""
        try:
            update_data = TickerScoreUpdate(status=status.value)
            return await self.update(score_id, update_data)
        except Exception as e:
            logger.error(f"更新评分状态失败: {e}")
            raise 