"""
市场仓储类
实现市场的数据访问和持久化操作
"""

import logging
from typing import List, Optional, Type, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.entities import Market, MarketStatus
from app.entities.market import MarketCreate, MarketUpdate
from app.repositories.base_repository import BaseRepository
from app.services.database_service import DatabaseService

logger = logging.getLogger(__name__)

class MarketRepository(BaseRepository[Market, MarketCreate, MarketUpdate]):
    """
    市场仓储类
    
    提供市场的数据访问和查询功能
    """
    
    def __init__(self, db_service: DatabaseService):
        super().__init__(db_service)
    
    @property
    def table_name(self) -> str:
        return "markets"
    
    @property
    def entity_class(self) -> Type[Market]:
        return Market
    
    @property
    def create_class(self) -> Type[MarketCreate]:
        return MarketCreate
    
    @property
    def update_class(self) -> Type[MarketUpdate]:
        return MarketUpdate
    
    def get_json_fields(self) -> List[str]:
        """JSON字段列表"""
        return []  # market表没有JSON字段
    
    async def get_by_code(self, code: str) -> Optional[Market]:
        """根据市场代码获取市场"""
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE code = :code
        """
        data = await self._execute_query_one(sql, {"code": code})
        if data:
            return self._dict_to_entity(data)
        return None
    
    async def get_by_region(self, region: str) -> List[Market]:
        """根据地区获取市场列表"""
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE region = :region
            ORDER BY code
        """
        rows = await self._execute_query(sql, {"region": region})
        return [self._dict_to_entity(row) for row in rows]
    
    async def get_active_markets(self) -> List[Market]:
        """获取活跃市场列表"""
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE status = :status
            ORDER BY code
        """
        rows = await self._execute_query(sql, {"status": MarketStatus.ACTIVE.value})
        return [self._dict_to_entity(row) for row in rows]
    
    async def search_markets(
        self, 
        keyword: str, 
        region: Optional[str] = None,
        limit: int = 50, 
        offset: int = 0
    ) -> List[Market]:
        """搜索市场"""
        try:
            where_clause = "(code LIKE :keyword OR name LIKE :keyword)"
            params = {
                "keyword": f"%{keyword}%",
                "limit": limit,
                "offset": offset
            }
            
            if region:
                where_clause += " AND region = :region"
                params["region"] = region
            
            sql = f"""
                SELECT * FROM {self.table_name}
                WHERE {where_clause}
                ORDER BY code
                LIMIT :limit OFFSET :offset
            """
            
            rows = await self._execute_query(sql, params)
            return [self._dict_to_entity(row) for row in rows]
            
        except Exception as e:
            logger.error(f"搜索市场失败: {e}")
            raise
    
    async def get_market_statistics(self) -> Dict[str, Any]:
        """获取市场统计信息"""
        try:
            sql = """
                SELECT 
                    COUNT(*) as total_count,
                    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_count,
                    COUNT(CASE WHEN status = 'inactive' THEN 1 END) as inactive_count,
                    COUNT(CASE WHEN status = 'suspended' THEN 1 END) as suspended_count,
                    COUNT(DISTINCT region) as region_count,
                    COUNT(DISTINCT currency) as currency_count
                FROM markets
            """
            
            result = await self._execute_query_one(sql)
            if result:
                return {
                    "total_count": result.get("total_count", 0),
                    "active_count": result.get("active_count", 0),
                    "inactive_count": result.get("inactive_count", 0),
                    "suspended_count": result.get("suspended_count", 0),
                    "region_count": result.get("region_count", 0),
                    "currency_count": result.get("currency_count", 0)
                }
            return {}
            
        except Exception as e:
            logger.error(f"获取市场统计信息失败: {e}")
            return {}
    
    async def get_markets_by_currency(self, currency: str) -> List[Market]:
        """根据货币获取市场列表"""
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE currency = :currency
            ORDER BY code
        """
        rows = await self._execute_query(sql, {"currency": currency})
        return [self._dict_to_entity(row) for row in rows]
    
    async def update_market_status(self, market_id: int, status: MarketStatus) -> Optional[Market]:
        """更新市场状态"""
        try:
            update_data = MarketUpdate(status=status.value)
            return await self.update(market_id, update_data)
        except Exception as e:
            logger.error(f"更新市场状态失败: {e}")
            raise
    
    async def get_markets_by_trading_days(self, trading_day: str) -> List[Market]:
        """根据交易日获取市场列表"""
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE trading_days LIKE :trading_day
            ORDER BY code
        """
        rows = await self._execute_query(sql, {"trading_day": f"%{trading_day}%"})
        return [self._dict_to_entity(row) for row in rows]
    
    async def get_markets_by_timezone(self, timezone: str) -> List[Market]:
        """根据时区获取市场列表"""
        sql = f"""
            SELECT * FROM {self.table_name}
            WHERE timezone = :timezone
            ORDER BY code
        """
        rows = await self._execute_query(sql, {"timezone": timezone})
        return [self._dict_to_entity(row) for row in rows]
    
    async def get_market_regions(self) -> List[str]:
        """获取所有市场地区"""
        sql = f"""
            SELECT DISTINCT region 
            FROM {self.table_name}
            ORDER BY region
        """
        rows = await self._execute_query(sql)
        return [row["region"] for row in rows]
    
    async def get_market_currencies(self) -> List[str]:
        """获取所有市场货币"""
        sql = f"""
            SELECT DISTINCT currency 
            FROM {self.table_name}
            ORDER BY currency
        """
        rows = await self._execute_query(sql)
        return [row["currency"] for row in rows]
    
    async def get_market_timezones(self) -> List[str]:
        """获取所有市场时区"""
        sql = f"""
            SELECT DISTINCT timezone 
            FROM {self.table_name}
            ORDER BY timezone
        """
        rows = await self._execute_query(sql)
        return [row["timezone"] for row in rows] 