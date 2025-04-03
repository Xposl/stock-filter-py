from typing import Dict, Any, List, Optional
from core.service.ticker_valuation_repository import TickerValuationRepository
from core.valuation import Valuation

class TickerValuation:
    """
    基于估值模型的股票估值处理类
    """
    updateTime = ''
    valuations = None

    def __init__(self, updateTime: str, valuations=None):
        """
        初始化TickerValuation处理类
        
        Args:
            updateTime: 更新时间
            valuations: 可选的估值模型列表
            db_connection: 可选的数据库连接
        """
        self.updateTime = updateTime
        if valuations is not None:
            self.valuations = valuations

    def calculate(self, ticker: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算股票的估值
        
        Args:
            ticker: 股票信息
            
        Returns:
            估值结果字典
        """
        return Valuation(self.updateTime, self.valuations).calculate(ticker)

    def update_ticker_valuation(self, ticker) -> Dict[str, Any]:
        """
        更新股票估值并保存到数据库
        
        Args:
            ticker: 股票对象
            
        Returns:
            估值结果字典
        """
        valuations = self.calculate(ticker)
        for valuationKey in valuations:
            result = valuations[valuationKey]
            if result is not None and isinstance(result, dict):
                # 确保 updateTime 是字符串格式
                time_key = self.updateTime.strftime('%Y-%m-%d') if hasattr(self.updateTime, 'strftime') else str(self.updateTime)
                TickerValuationRepository().update_item(ticker.id, valuationKey, time_key, result)
        return valuations
