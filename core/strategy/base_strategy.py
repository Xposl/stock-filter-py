"""
策略基类模块
"""
from abc import ABC, abstractmethod

from core.schema.k_line import KLine


class BaseStrategy(ABC):
    """策略基类，定义了策略类的基本接口"""

    def get_params(self):
        """获取策略参数，可选实现

        Returns:
            dict: 策略参数字典
        """
        return {}

    @abstractmethod
    def set_params(self, param: dict):
        """设置策略参数，可选实现

        Args:
            param (dict): 参数字典
        """
        pass

    @abstractmethod
    def get_key(self) -> str:
        """获取策略键名，必须实现

        Returns:
            str: 策略键名
        """
        pass

    @abstractmethod
    def calculate(self, kl_data: list[KLine]):
        """计算策略结果，必须实现

        Args:
            kl_data (list): K线数据列表

        Returns:
            list: 策略计算结果
        """
        pass
