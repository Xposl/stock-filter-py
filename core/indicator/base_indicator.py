from abc import ABC, abstractmethod

from core.enum.indicator_group import IndicatorGroup


class BaseIndicator(ABC):
    @abstractmethod
    def get_key(self) -> str:
        """返回指标唯一键名"""
        pass

    @abstractmethod
    def get_group(self) -> IndicatorGroup:
        """返回指标分组"""
        pass

    @abstractmethod
    def calculate(self, kl_data) -> dict:
        """计算指标，返回 dict(posData, score)"""
        pass
