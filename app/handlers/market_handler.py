"""
市场处理器
实现市场相关的业务逻辑
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, time

from app.entities import Market, MarketStatus
from app.entities.market import MarketCreate, MarketUpdate, MarketDTO
from app.repositories.market_repository import MarketRepository
from app.services.database_service import get_database_service
from app.handlers.base_handler import BaseHandler

logger = logging.getLogger(__name__)

class MarketHandler(BaseHandler):
    """市场业务逻辑处理器"""
    
    def __init__(self):
        super().__init__()
        self.db_service = get_database_service()
        self.market_repo = MarketRepository(self.db_service)
    
    async def create_market(
        self,
        code: str,
        name: str,
        region: str,
        timezone: str,
        open_time: time,
        close_time: time,
        currency: str = "USD",
        trading_days: str = "Mon,Tue,Wed,Thu,Fri",
        status: str = "active"
    ) -> Market:
        """创建新市场
        
        Args:
            code: 市场代码
            name: 市场名称
            region: 地区
            timezone: 时区
            open_time: 开盘时间
            close_time: 收盘时间
            currency: 货币代码
            trading_days: 交易日
            status: 市场状态
            
        Returns:
            创建的市场实体
        """
        try:
            # 验证必填字段
            self._validate_required_field(code, "市场代码")
            self._validate_required_field(name, "市场名称")
            self._validate_required_field(region, "地区")
            self._validate_required_field(timezone, "时区")
            
            # 验证市场代码格式
            self._validate_market_code(code)
            
            # 验证市场状态
            valid_statuses = [s.value for s in MarketStatus]
            if status not in valid_statuses:
                raise ValueError(f"status必须是以下值之一: {valid_statuses}")
            
            # 检查市场代码是否已存在
            existing_market = await self.market_repo.get_by_code(code)
            if existing_market:
                raise ValueError(f"市场代码已存在: {code}")
            
            # 创建市场数据
            market_data = {
                "code": code.strip().upper(),
                "name": name.strip(),
                "region": region.strip(),
                "timezone": timezone.strip(),
                "open_time": open_time,
                "close_time": close_time,
                "currency": currency.strip(),
                "trading_days": trading_days,
                "status": status
            }
            
            # 使用字典创建实体
            create_model = MarketCreate(**market_data)
            
            # 创建市场
            market = await self.market_repo.create(create_model)
            
            self._log_operation("create", str(market.id), "system", {"code": code, "name": name})
            logger.info(f"✅ 创建市场: {market.id}, 代码: {code}, 名称: {name}")
            return market
            
        except Exception as e:
            logger.error(f"❌ 创建市场失败: {e}")
            raise ValueError(f"创建市场失败: {e}") from e
    
    async def get_market_by_id(
        self,
        market_id: int
    ) -> Optional[Market]:
        """
        根据ID获取市场
        
        Args:
            market_id: 市场ID
            
        Returns:
            市场实体或None
        """
        try:
            market = await self.market_repo.get_by_id(market_id)
            
            if market:
                logger.info(f"✅ 获取市场: {market_id}")
            else:
                logger.warning(f"⚠️ 市场不存在: {market_id}")
            
            return market
                
        except Exception as e:
            logger.error(f"❌ 获取市场失败: {e}")
            raise Exception(f"获取市场失败: {str(e)}")
    
    async def get_market_by_code(
        self,
        code: str
    ) -> Optional[Market]:
        """
        根据市场代码获取市场
        
        Args:
            code: 市场代码
            
        Returns:
            市场实体或None
        """
        try:
            market = await self.market_repo.get_by_code(code)
            
            if market:
                logger.info(f"✅ 获取市场: {code}")
            else:
                logger.warning(f"⚠️ 市场不存在: {code}")
            
            return market
                
        except Exception as e:
            logger.error(f"❌ 获取市场失败: {e}")
            raise Exception(f"获取市场失败: {str(e)}")
    
    async def search_markets(
        self,
        keyword: str,
        region: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Market], int]:
        """
        搜索市场
        
        Args:
            keyword: 搜索关键词
            region: 地区过滤
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            (匹配的市场列表, 总数)
        """
        try:
            if not keyword or not keyword.strip():
                # 如果没有关键词，返回空结果
                return [], 0
            
            keyword = keyword.strip()
            
            # 使用Repository的搜索方法
            markets = await self.market_repo.search_markets(
                keyword=keyword,
                region=region,
                limit=limit,
                offset=offset
            )
            
            # 计算搜索结果总数（简化实现）
            total = len(markets)
            
            logger.info(f"✅ 搜索市场: 关键词: {keyword}, 地区: {region}, 结果: {len(markets)}")
            return markets, total
            
        except Exception as e:
            logger.error(f"❌ 搜索市场失败: {e}")
            raise Exception(f"搜索市场失败: {str(e)}")
    
    async def get_active_markets(self) -> Tuple[List[Market], int]:
        """
        获取活跃市场列表
        
        Returns:
            (市场列表, 总数)
        """
        try:
            markets = await self.market_repo.get_active_markets()
            total = len(markets)
            
            logger.info(f"✅ 获取活跃市场: 数量: {len(markets)}")
            return markets, total
            
        except Exception as e:
            logger.error(f"❌ 获取活跃市场失败: {e}")
            raise Exception(f"获取活跃市场失败: {str(e)}")
    
    async def get_markets_by_region(
        self,
        region: str
    ) -> Tuple[List[Market], int]:
        """
        根据地区获取市场列表
        
        Args:
            region: 地区
            
        Returns:
            (市场列表, 总数)
        """
        try:
            markets = await self.market_repo.get_by_region(region)
            total = len(markets)
            
            logger.info(f"✅ 获取地区市场: {region}, 数量: {len(markets)}")
            return markets, total
            
        except Exception as e:
            logger.error(f"❌ 获取地区市场失败: {e}")
            raise Exception(f"获取地区市场失败: {str(e)}")
    
    async def update_market(
        self,
        market_id: int,
        name: Optional[str] = None,
        region: Optional[str] = None,
        timezone: Optional[str] = None,
        open_time: Optional[time] = None,
        close_time: Optional[time] = None,
        currency: Optional[str] = None,
        trading_days: Optional[str] = None,
        status: Optional[str] = None
    ) -> Optional[Market]:
        """
        更新市场信息
        
        Args:
            market_id: 市场ID
            name: 新名称
            region: 新地区
            timezone: 新时区
            open_time: 新开盘时间
            close_time: 新收盘时间
            currency: 新货币代码
            trading_days: 新交易日
            status: 新状态
            
        Returns:
            更新后的市场实体
        """
        try:
            # 先获取市场验证存在性
            market = await self.market_repo.get_by_id(market_id)
            if not market:
                logger.warning(f"⚠️ 市场不存在: {market_id}")
                return None
            
            # 准备更新数据
            update_data = {}
            if name is not None:
                self._validate_required_field(name, "市场名称")
                update_data["name"] = name.strip()
            
            if region is not None:
                self._validate_required_field(region, "地区")
                update_data["region"] = region.strip()
            
            if timezone is not None:
                self._validate_required_field(timezone, "时区")
                update_data["timezone"] = timezone.strip()
            
            if open_time is not None:
                update_data["open_time"] = open_time
            
            if close_time is not None:
                update_data["close_time"] = close_time
            
            if currency is not None:
                update_data["currency"] = currency.strip()
            
            if trading_days is not None:
                update_data["trading_days"] = trading_days
            
            if status is not None:
                valid_statuses = [s.value for s in MarketStatus]
                if status not in valid_statuses:
                    raise ValueError(f"status必须是以下值之一: {valid_statuses}")
                update_data["status"] = status
            
            # 如果没有任何更新数据，返回原市场
            if not update_data:
                logger.info(f"✅ 无更新数据，返回原市场: {market_id}")
                return market
            
            # 执行更新
            update_model = MarketUpdate(**update_data)
            updated_market = await self.market_repo.update(
                market.id, update_model
            )
            
            self._log_operation("update", str(market_id), "system", update_data)
            logger.info(f"✅ 更新市场: {market_id}")
            return updated_market
                
        except Exception as e:
            logger.error(f"❌ 更新市场失败: {e}")
            raise Exception(f"更新市场失败: {str(e)}")
    
    async def delete_market(
        self,
        market_id: int,
        soft_delete: bool = True
    ) -> bool:
        """
        删除市场
        
        Args:
            market_id: 市场ID
            soft_delete: 是否软删除（更新状态）
            
        Returns:
            删除是否成功
        """
        try:
            # 验证存在性
            market = await self.market_repo.get_by_id(market_id)
            if not market:
                logger.warning(f"⚠️ 市场不存在: {market_id}")
                return False
            
            if soft_delete:
                # 软删除：更新状态为已删除
                update_data = MarketUpdate(status=MarketStatus.INACTIVE.value)
                await self.market_repo.update(market.id, update_data)
                logger.info(f"✅ 软删除市场: {market_id}")
            else:
                # 硬删除：物理删除记录
                success = await self.market_repo.delete(market.id)
                if success:
                    logger.info(f"✅ 硬删除市场: {market_id}")
                else:
                    logger.error(f"❌ 硬删除市场失败: {market_id}")
                    return False
            
            self._log_operation("delete", str(market_id), "system", {"soft_delete": soft_delete})
            return True
                
        except Exception as e:
            logger.error(f"❌ 删除市场失败: {e}")
            raise Exception(f"删除市场失败: {str(e)}")
    
    async def get_market_statistics(self) -> Dict[str, Any]:
        """
        获取市场统计信息
        
        Returns:
            统计信息字典
        """
        try:
            stats = await self.market_repo.get_market_statistics()
            
            logger.info(f"✅ 获取市场统计信息")
            return stats
                
        except Exception as e:
            logger.error(f"❌ 获取市场统计信息失败: {e}")
            return {
                "total_count": 0,
                "active_count": 0,
                "inactive_count": 0,
                "suspended_count": 0,
                "region_count": 0,
                "currency_count": 0,
                "error": str(e)
            }
    
    async def get_market_regions(self) -> List[str]:
        """
        获取所有市场地区
        
        Returns:
            地区列表
        """
        try:
            regions = await self.market_repo.get_market_regions()
            
            logger.info(f"✅ 获取市场地区: {len(regions)}")
            return regions
            
        except Exception as e:
            logger.error(f"❌ 获取市场地区失败: {e}")
            raise Exception(f"获取市场地区失败: {str(e)}")
    
    async def get_market_currencies(self) -> List[str]:
        """
        获取所有市场货币
        
        Returns:
            货币列表
        """
        try:
            currencies = await self.market_repo.get_market_currencies()
            
            logger.info(f"✅ 获取市场货币: {len(currencies)}")
            return currencies
            
        except Exception as e:
            logger.error(f"❌ 获取市场货币失败: {e}")
            raise Exception(f"获取市场货币失败: {str(e)}")
    
    async def get_markets_by_currency(
        self,
        currency: str
    ) -> Tuple[List[Market], int]:
        """
        根据货币获取市场列表
        
        Args:
            currency: 货币代码
            
        Returns:
            (市场列表, 总数)
        """
        try:
            markets = await self.market_repo.get_markets_by_currency(currency)
            total = len(markets)
            
            logger.info(f"✅ 获取货币市场: {currency}, 数量: {len(markets)}")
            return markets, total
            
        except Exception as e:
            logger.error(f"❌ 获取货币市场失败: {e}")
            raise Exception(f"获取货币市场失败: {str(e)}")
    
    def _validate_market_code(self, code: str) -> None:
        """
        验证市场代码格式
        
        Args:
            code: 市场代码
            
        Raises:
            ValueError: 格式错误时抛出
        """
        if not code or not code.strip():
            raise ValueError("市场代码不能为空")
        
        # 验证代码长度
        if len(code) < 1 or len(code) > 10:
            raise ValueError("市场代码长度必须在1-10字符之间")
        
        # 验证代码格式（只允许字母、数字、下划线）
        import re
        if not re.match(r'^[A-Za-z0-9_]+$', code):
            raise ValueError("市场代码只能包含字母、数字和下划线")

# 单例模式 - 保存handler实例
_market_handler_instance = None

def get_market_handler() -> MarketHandler:
    """获取市场处理器实例 (单例模式)"""
    global _market_handler_instance
    if _market_handler_instance is None:
        _market_handler_instance = MarketHandler()
    return _market_handler_instance 