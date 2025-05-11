from abc import ABC, abstractmethod

class BaseScore(ABC):
    @abstractmethod
    def calculate(self, ticker, kLineData=None, strategyData=None, indicatorData=None, valuationData=None):
        """计算评分，返回评分结果"""
        pass 