from abc import ABC, abstractmethod


class BaseValuation(ABC):
    @abstractmethod
    def getKey(self):
        """返回估值模型唯一键名"""
        pass

    @abstractmethod
    def calculate(self, ticker):
        """计算估值，返回估值结果"""
        pass
