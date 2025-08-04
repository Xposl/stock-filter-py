"""
股票指标处理器
负责股票指标的计算和数据库更新
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from app.entities.ticker_indicator import TickerIndicator, TickerIndicatorCreate, TickerIndicatorUpdate
from app.entities.ticker import Ticker
from app.handlers.base_handler import BaseHandler
from app.repositories.ticker_indicator_repository import TickerIndicatorRepository
from app.services.database_service import get_database_service
from core.enum.ticker_k_type import TickerKType
from core.indicator import Indicator


class TickerIndicatorHandler(BaseHandler):
    """
    股票指标处理器类
    负责股票指标的计算、更新和管理
    """
    
    def __init__(self):
        """初始化处理器"""
        super().__init__()
        self.db_service = get_database_service()
        self.indicator_repo = TickerIndicatorRepository(self.db_service)
        self.update_time = ""
        self.indicators = None
    
    def set_update_time(self, update_time: str):
        """设置更新时间"""
        self.update_time = update_time
    
    def set_indicators(self, indicators: Optional[List] = None):
        """设置指标列表"""
        if indicators is not None:
            self.indicators = indicators
    
    def calculate(self, k_line_data: Optional[List] = None) -> Dict[str, Any]:
        """
        计算指标
        
        Args:
            k_line_data: K线数据列表
            
        Returns:
            计算后的指标结果
        """
        if not self.indicators:
            raise ValueError("指标列表未设置")
        
        return Indicator(self.indicators).calculate(k_line_data)
    
    async def update_ticker_indicator(
        self, 
        ticker: Ticker, 
        k_line_data: Optional[List] = None
    ) -> Dict[str, Any]:
        """
        更新股票指标
        
        Args:
            ticker: 股票对象
            k_line_data: K线数据列表
            
        Returns:
            更新后的指标结果
        """
        if not k_line_data or len(k_line_data) == 0:
            self.logger.warning(f"股票 {ticker.code} 无K线数据")
            return {}
        
        # 计算指标
        indicators = self.calculate(k_line_data)
        
        # 更新数据库
        for indicator_key, result in indicators.items():
            await self._update_indicator_in_db(
                ticker.id, 
                indicator_key, 
                TickerKType.DAY.value, 
                self.update_time, 
                result
            )
        
        return indicators
    
    async def _update_indicator_in_db(
        self, 
        ticker_id: int, 
        indicator_key: str, 
        kl_type: str, 
        time_key: str, 
        result: Any
    ):
        """
        更新数据库中的指标数据
        
        Args:
            ticker_id: 股票ID
            indicator_key: 指标键名
            kl_type: K线类型
            time_key: 时间键
            result: 计算结果
        """
        try:
            # 检查是否已存在
            existing_indicator = await self.indicator_repo.get_by_ticker_and_key(
                ticker_id, indicator_key, kl_type
            )
            
            if existing_indicator:
                # 更新现有记录
                update_data = TickerIndicatorUpdate(
                    time_key=time_key,
                    history=result,
                    version=existing_indicator.version + 1
                )
                await self.indicator_repo.update(existing_indicator.id, update_data)
                self.logger.info(f"更新指标 {indicator_key} 成功")
            else:
                # 创建新记录
                create_data = TickerIndicatorCreate(
                    ticker_id=ticker_id,
                    indicator_key=indicator_key,
                    kl_type=kl_type,
                    time_key=time_key,
                    history=result,
                    code=f"{ticker_id}_{indicator_key}_{kl_type}"
                )
                await self.indicator_repo.create(create_data)
                self.logger.info(f"创建指标 {indicator_key} 成功")
                
        except Exception as e:
            self.logger.error(f"更新指标 {indicator_key} 失败: {str(e)}")
            raise
    
    async def get_ticker_indicators(
        self, 
        ticker_id: int, 
        indicator_key: Optional[str] = None,
        kl_type: Optional[str] = None
    ) -> List[TickerIndicator]:
        """
        获取股票指标列表
        
        Args:
            ticker_id: 股票ID
            indicator_key: 指标键名（可选）
            kl_type: K线类型（可选）
            
        Returns:
            指标列表
        """
        return await self.indicator_repo.get_by_ticker_id(ticker_id, indicator_key, kl_type)
    
    async def get_indicator_by_key(
        self, 
        ticker_id: int, 
        indicator_key: str, 
        kl_type: str
    ) -> Optional[TickerIndicator]:
        """
        根据键名获取指标
        
        Args:
            ticker_id: 股票ID
            indicator_key: 指标键名
            kl_type: K线类型
            
        Returns:
            指标对象或None
        """
        return await self.indicator_repo.get_by_ticker_and_key(ticker_id, indicator_key, kl_type)
    
    async def delete_indicator(
        self, 
        ticker_id: int, 
        indicator_key: str, 
        kl_type: str
    ) -> bool:
        """
        删除指标
        
        Args:
            ticker_id: 股票ID
            indicator_key: 指标键名
            kl_type: K线类型
            
        Returns:
            是否删除成功
        """
        indicator = await self.get_indicator_by_key(ticker_id, indicator_key, kl_type)
        if indicator:
            await self.indicator_repo.delete(indicator.id)
            self.logger.info(f"删除指标 {indicator_key} 成功")
            return True
        return False


# 单例模式
_ticker_indicator_handler_instance = None


def get_ticker_indicator_handler() -> TickerIndicatorHandler:
    """获取TickerIndicatorHandler单例实例"""
    global _ticker_indicator_handler_instance
    if _ticker_indicator_handler_instance is None:
        _ticker_indicator_handler_instance = TickerIndicatorHandler()
    return _ticker_indicator_handler_instance 