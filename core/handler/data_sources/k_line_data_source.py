"""
数据源模块初始化文件
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union
import pandas as pd


class KLine:
    """K线数据"""
    time_key: str
    high: float
    low: float
    open: float
    close: float
    volume: float
    turnover: float
    turnover_rate: float

class KLineDataSource(ABC):
    """K线数据源基类，定义了数据源需要实现的接口"""
    
    @abstractmethod
    def get_data_time_key(self, data: Any, index: int) -> str:
        """获取数据时间键
        
        Args:
            data: K线数据
            index: 数据索引
            
        Returns:
            str: 时间键
        """
        pass

    @abstractmethod
    def convert_data(self, data: Any, index: int) -> Dict[str, Any]:
        """转换K线数据为统一格式
        
        Args:
            data: K线数据
            index: 数据索引
            
        Returns:
            dict: 标准格式的K线数据
        """
        pass

    @abstractmethod
    def get_on_time_kl(self) -> Optional[Dict[str, Any]]:
        """获取实时K线数据
        
        Returns:
            dict: 标准格式的K线数据，失败返回None
        """
        pass

    @abstractmethod
    def get_kl(self) -> list[KLine]:
        """获取K线数据
        
        Returns:
            dict或DataFrame: K线数据，失败返回None
        """
        pass