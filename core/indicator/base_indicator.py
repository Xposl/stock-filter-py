from abc import ABC, abstractmethod

class BaseIndicator(ABC):
    @abstractmethod
    def getKey(self):
        """返回指标唯一键名"""
        pass

    @abstractmethod
    def getGroup(self):
        """返回指标分组"""
        pass

    @abstractmethod
    def calculate(self, klData):
        """计算指标，返回 dict(posData, score)"""
        pass 