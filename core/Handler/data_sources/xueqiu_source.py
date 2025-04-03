"""
雪球数据源K线数据处理模块
"""
import datetime
import math
from typing import Dict, Any, Optional, Union
import pandas as pd

from .xueqiu_api import Xueqiu

from . import KLineDataSource

class XueqiuKLineSource(KLineDataSource):
    """雪球数据源K线数据处理类"""
    
    def __init__(self, code, start_date=None, end_date=None):
        """初始化数据源
        
        Args:
            code: 股票代码
            start_date: 开始日期，可选
            end_date: 结束日期，可选
        """
        self.code = code
        self.start_date = start_date
        self.end_date = end_date
        self.xueqiu = Xueqiu()

    def get_data_time_key(self, data: Any, index: int) -> str:
        """获取数据时间键
        
        Args:
            data: K线数据
            index: 数据索引
            
        Returns:
            str: 时间键
        """
        timestamp = data['日期'][index]
        return datetime.datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d')

    def convert_data(self, data: Any, index: int) -> Dict[str, Any]:
        """转换K线数据为统一格式
        
        Args:
            data: K线数据
            index: 数据索引
            
        Returns:
            dict: 标准格式的K线数据
        """
        return {
            'time_key': self.get_data_time_key(data, index),
            'high': data['最高'][index],
            'low': data['最低'][index],
            'open': data['开盘'][index],
            'close': data['收盘'][index],
            'volume': data['成交量'][index],
            'turnover': 0 if math.isnan(data['成交额'][index]) else data['成交额'][index],
            'turnover_rate': 0 if math.isnan(data['换手率'][index]) else data['换手率'][index]
        }

    def get_kline_data(self):
        """获取历史K线数据
        
        Returns:
            DataFrame: K线数据
        """
        # 如果没有提供开始日期，使用今天作为开始日期
        start_date = self.start_date if self.start_date else datetime.date.today().strftime('%Y-%m-%d')
        
        if self.code.startswith('US') or self.code.startswith('HK'):
            data = self.xueqiu.getStockHistory(self.code[3:], start_date)
        elif self.code.startswith('SZ'):
            data = self.xueqiu.getStockHistory('SZ'+self.code[3:], start_date)
        elif self.code.startswith('SH'):
            data = self.xueqiu.getStockHistory('SH'+self.code[3:], start_date)
        return data

    def get_on_time_kl(self) -> Optional[Dict[str, Any]]:
        """获取实时K线数据
        
        Returns:
            dict: 标准格式的K线数据
        """
        try:
            stock_code = ""
            if self.code.startswith('US') or self.code.startswith('HK'):
                stock_code = self.code[3:]
            elif self.code.startswith('SZ'):
                stock_code = 'SZ' + self.code[3:]
            elif self.code.startswith('SH'):
                stock_code = 'SH' + self.code[3:]
                
            quote = self.xueqiu.getStockQuote(stock_code)
            if quote:
                return {
                    'time_key': datetime.date.today(),
                    'high': quote.get('high', 0),
                    'low': quote.get('low', 0),
                    'open': quote.get('open', 0),
                    'close': quote.get('current', 0),
                    'volume': quote.get('volume', 0),
                    'turnover': quote.get('amount', 0),
                    'turnover_rate': quote.get('turnover_rate', 0),
                    'id': 0
                }
            return None
        except Exception as e:
            print(f"获取雪球实时数据失败: {e}")
            return None
            
    def get_kl(self) -> Optional[Union[Dict[str, Any], pd.DataFrame]]:
        """获取K线数据
        
        Returns:
            dict或DataFrame: K线数据
        """
        # 优先尝试获取实时数据
        real_time_data = self.get_on_time_kl()
        if real_time_data:
            return real_time_data
            
        # 如果实时数据获取失败且有日期范围，尝试获取历史数据
        if self.start_date:
            return self.get_kline_data()
        return None
