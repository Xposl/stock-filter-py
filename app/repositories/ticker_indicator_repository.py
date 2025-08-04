"""
股票指标仓储类
实现股票指标的数据访问和持久化操作
"""

import logging
from typing import List, Optional, Type, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.entities import TickerIndicator, IndicatorStatus
from app.entities.ticker_indicator import TickerIndicatorCreate, TickerIndicatorUpdate
from app.repositories.base_repository import BaseRepository
from app.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

class TickerIndicatorRepository(BaseRepository[TickerIndicator, TickerIndicatorCreate, TickerIndicatorUpdate]):
    """
    股票指标仓储类
    
    提供股票指标的数据访问和查询功能
    """
    
    def __init__(self, db_service: DatabaseService):
        super().__init__(db_service)
    
    @property
    def table_name(self) -> str:
        return "ticker_indicators"
    
    @property
    def entity_class(self) -> Type[TickerIndicator]:
        return TickerIndicator
    
    @property
    def create_class(self) -> Type[TickerIndicatorCreate]:
        return TickerIndicatorCreate
    
    @property
    def update_class(self) -> Type[TickerIndicatorUpdate]:
        return TickerIndicatorUpdate
    
    def get_json_fields(self) -> List[str]:
        """JSON字段列表"""
        return ["history"]  # ticker_indicators表的JSON字段
    
    async def get_by_ticker_id_and_indicator_key(
        self, 
        ticker_id: int, 
        indicator_key: str, 
        kl_type: str
    ) -> Optional[TickerIndicator]:
        """根据股票ID、指标键和K线类型获取指标"""
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE ticker_id = :ticker_id 
            AND indicator_key = :indicator_key 
            AND kl_type = :kl_type
        """
        data = await self._execute_query_one(sql, {
            "ticker_id": ticker_id,
            "indicator_key": indicator_key,
            "kl_type": kl_type
        })
        if data:
            return self._dict_to_entity(data)
        return None
    
    async def get_by_ticker_id_and_kl_type(
        self, 
        ticker_id: int, 
        kl_type: str
    ) -> List[TickerIndicator]:
        """根据股票ID和K线类型获取所有指标"""
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE ticker_id = :ticker_id AND kl_type = :kl_type
            ORDER BY indicator_key
        """
        rows = await self._execute_query(sql, {
            "ticker_id": ticker_id,
            "kl_type": kl_type
        })
        return [self._dict_to_entity(row) for row in rows]
    
    async def get_by_indicator_key(
        self, 
        indicator_key: str, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[TickerIndicator]:
        """根据指标键获取指标列表"""
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE indicator_key = :indicator_key
            ORDER BY ticker_id, kl_type
            LIMIT :limit OFFSET :offset
        """
        rows = await self._execute_query(sql, {
            "indicator_key": indicator_key,
            "limit": limit,
            "offset": offset
        })
        return [self._dict_to_entity(row) for row in rows]
    
    async def get_by_kl_type(
        self, 
        kl_type: str, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[TickerIndicator]:
        """根据K线类型获取指标列表"""
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE kl_type = :kl_type
            ORDER BY ticker_id, indicator_key
            LIMIT :limit OFFSET :offset
        """
        rows = await self._execute_query(sql, {
            "kl_type": kl_type,
            "limit": limit,
            "offset": offset
        })
        return [self._dict_to_entity(row) for row in rows]
    
    async def get_active_indicators(
        self, 
        ticker_id: Optional[int] = None,
        limit: int = 100, 
        offset: int = 0
    ) -> List[TickerIndicator]:
        """获取活跃指标列表"""
        where_clause = "WHERE status = :status"
        params = {
            "status": IndicatorStatus.ACTIVE.value,
            "limit": limit,
            "offset": offset
        }
        
        if ticker_id:
            where_clause += " AND ticker_id = :ticker_id"
            params["ticker_id"] = ticker_id
        
        sql = f"""
            SELECT * FROM {self.table_name}
            {where_clause}
            ORDER BY ticker_id, indicator_key, kl_type
            LIMIT :limit OFFSET :offset
        """
        
        rows = await self._execute_query(sql, params)
        return [self._dict_to_entity(row) for row in rows]
    
    async def search_indicators(
        self, 
        keyword: str, 
        ticker_id: Optional[int] = None,
        kl_type: Optional[str] = None,
        limit: int = 50, 
        offset: int = 0
    ) -> List[TickerIndicator]:
        """搜索指标"""
        try:
            where_conditions = ["(indicator_key LIKE :keyword OR code LIKE :keyword)"]
            params = {
                "keyword": f"%{keyword}%",
                "limit": limit,
                "offset": offset
            }
            
            if ticker_id:
                where_conditions.append("ticker_id = :ticker_id")
                params["ticker_id"] = ticker_id
            
            if kl_type:
                where_conditions.append("kl_type = :kl_type")
                params["kl_type"] = kl_type
            
            where_clause = " AND ".join(where_conditions)
            
            sql = f"""
                SELECT * FROM {self.table_name}
                WHERE {where_clause}
                ORDER BY ticker_id, indicator_key
                LIMIT :limit OFFSET :offset
            """
            
            rows = await self._execute_query(sql, params)
            return [self._dict_to_entity(row) for row in rows]
            
        except Exception as e:
            logger.error(f"搜索指标失败: {e}")
            raise
    
    async def get_indicator_statistics(self) -> Dict[str, Any]:
        """获取指标统计信息"""
        try:
            sql = """
                SELECT 
                    COUNT(*) as total_count,
                    COUNT(CASE WHEN status = 1 THEN 1 END) as active_count,
                    COUNT(CASE WHEN status = 0 THEN 1 END) as inactive_count,
                    COUNT(CASE WHEN status = -1 THEN 1 END) as deleted_count,
                    COUNT(DISTINCT ticker_id) as ticker_count,
                    COUNT(DISTINCT indicator_key) as indicator_type_count,
                    COUNT(DISTINCT kl_type) as kl_type_count
                FROM ticker_indicators
            """
            
            result = await self._execute_query_one(sql)
            if result:
                return {
                    "total_count": result.get("total_count", 0),
                    "active_count": result.get("active_count", 0),
                    "inactive_count": result.get("inactive_count", 0),
                    "deleted_count": result.get("deleted_count", 0),
                    "ticker_count": result.get("ticker_count", 0),
                    "indicator_type_count": result.get("indicator_type_count", 0),
                    "kl_type_count": result.get("kl_type_count", 0)
                }
            return {}
            
        except Exception as e:
            logger.error(f"获取指标统计信息失败: {e}")
            return {}
    
    async def get_indicators_with_ticker_info(
        self, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取带股票信息的指标列表"""
        try:
            sql = f"""
                SELECT ti.*, t.code as ticker_code, t.name as ticker_name
                FROM {self.table_name} ti
                LEFT JOIN tickers t ON ti.ticker_id = t.id
                ORDER BY ti.ticker_id, ti.indicator_key
                LIMIT :limit OFFSET :offset
            """
            
            rows = await self._execute_query(sql, {"limit": limit, "offset": offset})
            return rows
            
        except Exception as e:
            logger.error(f"获取带股票信息的指标列表失败: {e}")
            raise
    
    async def get_latest_time_key_by_ticker(
        self, 
        ticker_id: int, 
        kl_type: str
    ) -> Optional[str]:
        """获取股票指标最新时间键"""
        try:
            sql = f"""
                SELECT MAX(time_key) as latest_time
                FROM {self.table_name}
                WHERE ticker_id = :ticker_id AND kl_type = :kl_type
            """
            
            result = await self._execute_query_one(sql, {
                "ticker_id": ticker_id,
                "kl_type": kl_type
            })
            
            return result.get("latest_time") if result else None
            
        except Exception as e:
            logger.error(f"获取最新时间键失败: {e}")
            return None
    
    async def update_indicator_status(
        self, 
        indicator_id: int, 
        status: IndicatorStatus
    ) -> Optional[TickerIndicator]:
        """更新指标状态"""
        try:
            update_data = TickerIndicatorUpdate(status=status.value)
            return await self.update(indicator_id, update_data)
        except Exception as e:
            logger.error(f"更新指标状态失败: {e}")
            raise
    
    async def soft_delete_indicator(
        self, 
        indicator_id: int
    ) -> Optional[TickerIndicator]:
        """软删除指标"""
        try:
            update_data = TickerIndicatorUpdate(status=IndicatorStatus.DELETED.value)
            return await self.update(indicator_id, update_data)
        except Exception as e:
            logger.error(f"软删除指标失败: {e}")
            raise
    
    async def restore_indicator(
        self, 
        indicator_id: int
    ) -> Optional[TickerIndicator]:
        """恢复指标"""
        try:
            update_data = TickerIndicatorUpdate(status=IndicatorStatus.ACTIVE.value)
            return await self.update(indicator_id, update_data)
        except Exception as e:
            logger.error(f"恢复指标失败: {e}")
            raise
    
    async def get_indicators_by_time_range(
        self, 
        start_time: str, 
        end_time: str,
        ticker_id: Optional[int] = None,
        limit: int = 100, 
        offset: int = 0
    ) -> List[TickerIndicator]:
        """根据时间范围获取指标"""
        try:
            where_conditions = ["time_key BETWEEN :start_time AND :end_time"]
            params = {
                "start_time": start_time,
                "end_time": end_time,
                "limit": limit,
                "offset": offset
            }
            
            if ticker_id:
                where_conditions.append("ticker_id = :ticker_id")
                params["ticker_id"] = ticker_id
            
            where_clause = " AND ".join(where_conditions)
            
            sql = f"""
                SELECT * FROM {self.table_name}
                WHERE {where_clause}
                ORDER BY time_key DESC
                LIMIT :limit OFFSET :offset
            """
            
            rows = await self._execute_query(sql, params)
            return [self._dict_to_entity(row) for row in rows]
            
        except Exception as e:
            logger.error(f"根据时间范围获取指标失败: {e}")
            raise 