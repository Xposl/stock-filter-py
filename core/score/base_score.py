from abc import ABC, abstractmethod

from core.models.ticker_score import TickerScore


class BaseScore(ABC):
    @abstractmethod
    def calculate(
        self,
        ticker,
        kLineData=None,
        strategyData=None,
        indicatorData=None,
        valuationData=None,
    ) -> list[TickerScore]:
        """计算评分，返回评分结果"""
        pass
