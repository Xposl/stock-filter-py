"""
股票估值处理器
负责股票估值的计算和数据库更新
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from app.entities.ticker_valuation import TickerValuation, TickerValuationCreate, TickerValuationUpdate
from app.entities.ticker import Ticker
from app.handlers.base_handler import BaseHandler
from app.repositories.ticker_valuation_repository import TickerValuationRepository
from app.services.database_service import get_database_service
from core.valuation import Valuation


class TickerValuationHandler(BaseHandler):
    """
    股票估值处理器类
    负责股票估值的计算、更新和管理
    """
    
    def __init__(self, update_time: str = "", valuations: Optional[List] = None):
        """
        初始化处理器
        
        Args:
            update_time: 更新时间
            valuations: 估值模型列表
        """
        super().__init__()
        self.db_service = get_database_service()
        self.valuation_repo = TickerValuationRepository(self.db_service)
        self.update_time = update_time
        self.valuations = valuations
    
    def set_update_time(self, update_time: str):
        """设置更新时间"""
        self.update_time = update_time
    
    def set_valuations(self, valuations: List):
        """设置估值模型列表"""
        self.valuations = valuations
    
    def calculate(self, ticker: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        计算股票估值
        
        Args:
            ticker: 股票信息字典
            
        Returns:
            估值结果字典
        """
        return Valuation(self.update_time, self.valuations).calculate(ticker)
    
    async def update_ticker_valuation(
        self, 
        ticker: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        更新股票估值并保存到数据库
        
        Args:
            ticker: 股票信息字典
            
        Returns:
            估值结果字典
        """
        if not ticker or "id" not in ticker:
            self.logger.error("股票信息不完整，缺少ID")
            return {}
        
        # 计算估值
        valuations = self.calculate(ticker)
        
        # 更新数据库
        for valuation_key, result in valuations.items():
            if result is not None and isinstance(result, dict):
                # 确保 updateTime 是字符串格式
                time_key = (
                    self.update_time.strftime("%Y-%m-%d")
                    if hasattr(self.update_time, "strftime")
                    else str(self.update_time)
                )
                
                await self._update_valuation_in_db(
                    ticker["id"], 
                    valuation_key, 
                    time_key, 
                    result
                )
        
        return valuations
    
    async def _update_valuation_in_db(
        self, 
        ticker_id: int, 
        valuation_key: str, 
        time_key: str, 
        result: Dict[str, Any]
    ):
        """
        更新数据库中的估值数据
        
        Args:
            ticker_id: 股票ID
            valuation_key: 估值键名
            time_key: 时间键
            result: 计算结果
        """
        try:
            # 检查是否已存在
            existing_valuation = await self.valuation_repo.get_by_ticker_and_key(
                ticker_id, valuation_key
            )
            
            if existing_valuation:
                # 更新现有记录
                update_data = TickerValuationUpdate(
                    time_key=time_key,
                    valuation_data=result,
                    version=existing_valuation.version + 1
                )
                await self.valuation_repo.update(existing_valuation.id, update_data)
                self.logger.info(f"更新估值 {valuation_key} 成功")
            else:
                # 创建新记录
                create_data = TickerValuationCreate(
                    ticker_id=ticker_id,
                    valuation_key=valuation_key,
                    time_key=time_key,
                    valuation_data=result,
                    code=f"{ticker_id}_{valuation_key}"
                )
                await self.valuation_repo.create(create_data)
                self.logger.info(f"创建估值 {valuation_key} 成功")
                
        except Exception as e:
            self.logger.error(f"更新估值 {valuation_key} 失败: {str(e)}")
            raise
    
    async def get_ticker_valuations(
        self, 
        ticker_id: int, 
        valuation_key: Optional[str] = None
    ) -> List[TickerValuation]:
        """
        获取股票估值列表
        
        Args:
            ticker_id: 股票ID
            valuation_key: 估值键名（可选）
            
        Returns:
            估值列表
        """
        return await self.valuation_repo.get_by_ticker_id(ticker_id, valuation_key)
    
    async def get_valuation_by_key(
        self, 
        ticker_id: int, 
        valuation_key: str
    ) -> Optional[TickerValuation]:
        """
        根据键名获取估值
        
        Args:
            ticker_id: 股票ID
            valuation_key: 估值键名
            
        Returns:
            估值对象或None
        """
        return await self.valuation_repo.get_by_ticker_and_key(ticker_id, valuation_key)
    
    async def get_latest_valuation(
        self, 
        ticker_id: int, 
        valuation_key: Optional[str] = None
    ) -> Optional[TickerValuation]:
        """
        获取最新估值
        
        Args:
            ticker_id: 股票ID
            valuation_key: 估值键名（可选）
            
        Returns:
            最新估值对象或None
        """
        return await self.valuation_repo.get_latest_by_ticker(ticker_id, valuation_key)
    
    async def delete_valuation(
        self, 
        ticker_id: int, 
        valuation_key: str
    ) -> bool:
        """
        删除估值
        
        Args:
            ticker_id: 股票ID
            valuation_key: 估值键名
            
        Returns:
            是否删除成功
        """
        valuation = await self.get_valuation_by_key(ticker_id, valuation_key)
        if valuation:
            await self.valuation_repo.delete(valuation.id)
            self.logger.info(f"删除估值 {valuation_key} 成功")
            return True
        return False
    
    async def get_valuation_statistics(
        self, 
        ticker_id: int, 
        valuation_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取估值统计信息
        
        Args:
            ticker_id: 股票ID
            valuation_key: 估值键名（可选）
            
        Returns:
            统计信息字典
        """
        valuations = await self.get_ticker_valuations(ticker_id, valuation_key)
        
        if not valuations:
            return {
                "count": 0,
                "latest_valuation": None,
                "valuation_types": []
            }
        
        # 获取估值类型
        valuation_types = list(set([v.valuation_key for v in valuations]))
        
        # 获取最新估值
        latest_valuation = valuations[-1] if valuations else None
        
        return {
            "count": len(valuations),
            "latest_valuation": latest_valuation,
            "valuation_types": valuation_types
        }
    
    async def calculate_and_update(
        self, 
        ticker: Dict[str, Any], 
        update_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        计算并更新估值（便捷方法）
        
        Args:
            ticker: 股票信息字典
            update_time: 更新时间（可选）
            
        Returns:
            估值结果字典
        """
        if update_time:
            self.set_update_time(update_time)
        
        return await self.update_ticker_valuation(ticker)


# 单例模式
_ticker_valuation_handler_instance = None


def get_ticker_valuation_handler(
    update_time: str = "", 
    valuations: Optional[List] = None
) -> TickerValuationHandler:
    """获取TickerValuationHandler单例实例"""
    global _ticker_valuation_handler_instance
    if _ticker_valuation_handler_instance is None:
        _ticker_valuation_handler_instance = TickerValuationHandler(update_time, valuations)
    elif update_time or valuations is not None:
        if update_time:
            _ticker_valuation_handler_instance.set_update_time(update_time)
        if valuations is not None:
            _ticker_valuation_handler_instance.set_valuations(valuations)
    return _ticker_valuation_handler_instance 