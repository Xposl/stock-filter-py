"""
统一股票数据提供者接口
定义标准化的股票数据访问接口，支持多个数据源
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, date
import pandas as pd
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class StockMarket(Enum):
    """股票市场枚举"""
    A_SHARE = "SH_SZ"  # A股（上海+深圳）
    HONG_KONG = "HK"   # 港股
    US = "US"          # 美股
    UK = "UK"          # 英股
    OTHER = "OTHER"    # 其他


class DataPeriod(Enum):
    """数据周期枚举"""
    MINUTE_1 = "1min"
    MINUTE_5 = "5min"
    MINUTE_15 = "15min"
    MINUTE_30 = "30min"
    HOUR_1 = "1hour"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class StockDataProvider(ABC):
    """股票数据提供者抽象基类"""
    
    def __init__(self, name: str, priority: int = 0):
        """
        初始化数据提供者
        
        Args:
            name: 提供者名称
            priority: 优先级（数字越大优先级越高）
        """
        self.name = name
        self.priority = priority
        self._is_available = True
        self._error_count = 0
        self._max_errors = 5  # 最大错误次数
    
    @property
    def is_available(self) -> bool:
        """检查提供者是否可用"""
        return self._is_available and self._error_count < self._max_errors
    
    def _handle_error(self, error: Exception, operation: str):
        """处理错误"""
        self._error_count += 1
        logger.error(f"{self.name} {operation} 失败: {error}")
        
        if self._error_count >= self._max_errors:
            self._is_available = False
            logger.warning(f"{self.name} 因连续错误过多已被标记为不可用")
    
    def reset_error_count(self):
        """重置错误计数"""
        self._error_count = 0
        self._is_available = True
    
    @abstractmethod
    def get_stock_info(self, symbol: str, market: StockMarket = None) -> Optional[Dict[str, Any]]:
        """
        获取股票基本信息
        
        Args:
            symbol: 股票代码
            market: 市场类型
            
        Returns:
            股票基本信息字典
        """
        pass
    
    @abstractmethod
    def get_stock_quote(self, symbol: str, market: StockMarket = None) -> Optional[Dict[str, Any]]:
        """
        获取股票实时行情
        
        Args:
            symbol: 股票代码
            market: 市场类型
            
        Returns:
            股票实时行情字典
        """
        pass
    
    @abstractmethod
    def get_stock_history(self, symbol: str, 
                         start_date: Union[str, date, datetime],
                         end_date: Union[str, date, datetime] = None,
                         period: DataPeriod = DataPeriod.DAILY,
                         market: StockMarket = None) -> Optional[pd.DataFrame]:
        """
        获取股票历史数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期（可选，默认为今天）
            period: 数据周期
            market: 市场类型
            
        Returns:
            历史数据DataFrame
        """
        pass
    
    @abstractmethod
    def get_company_info(self, symbol: str, market: StockMarket = None) -> Optional[Dict[str, Any]]:
        """
        获取公司详细信息
        
        Args:
            symbol: 股票代码
            market: 市场类型
            
        Returns:
            公司信息字典
        """
        pass
    
    @abstractmethod
    def search_stocks(self, keyword: str, market: StockMarket = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        搜索股票
        
        Args:
            keyword: 搜索关键词
            market: 市场类型
            limit: 返回结果数量限制
            
        Returns:
            股票搜索结果列表
        """
        pass
    
    @abstractmethod
    def get_supported_markets(self) -> List[StockMarket]:
        """
        获取支持的市场列表
        
        Returns:
            支持的市场类型列表
        """
        pass
    
    def normalize_symbol(self, symbol: str, market: StockMarket = None) -> str:
        """
        标准化股票代码
        
        Args:
            symbol: 原始股票代码
            market: 市场类型
            
        Returns:
            标准化后的股票代码
        """
        # 默认实现，子类可以重写
        return symbol.upper().strip()
    
    def __str__(self) -> str:
        return f"{self.name} (priority: {self.priority}, available: {self.is_available})"
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', priority={self.priority})"


class StockDataResponse:
    """股票数据响应包装类"""
    
    def __init__(self, data: Any, provider: str, success: bool = True, error: str = None):
        """
        初始化响应
        
        Args:
            data: 响应数据
            provider: 数据提供者名称
            success: 是否成功
            error: 错误信息
        """
        self.data = data
        self.provider = provider
        self.success = success
        self.error = error
        self.timestamp = datetime.now()
    
    def __bool__(self) -> bool:
        return self.success and self.data is not None
    
    def __repr__(self) -> str:
        return f"StockDataResponse(provider={self.provider}, success={self.success})" 