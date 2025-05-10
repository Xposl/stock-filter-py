"""
新浪数据源K线数据处理模块
"""
import akshare as ak
import datetime
import math
from typing import Dict, Any, Optional, Union
import pandas as pd

from .k_line_data_source import KLineDataSource

class SinaKLineSource(KLineDataSource):
    """新浪数据源K线数据处理类"""
    
    def __init__(self, code: str, start_date: Optional[str]=None, end_date: Optional[str]=None):
        """初始化数据源
        
        Args:
            code: 股票代码
            start_date: 开始日期，可选
            end_date: 结束日期，可选
        """
        self.code = code
        self.start_date = start_date
        self.end_date = end_date
        self.type = 0

    def get_data_time_key(self, data: Any, index: int) -> str:
        """获取数据时间键
        
        Args:
            data: K线数据
            index: 数据索引
            
        Returns:
            str: 时间键
        """
        if self.type == 1:
            return data.index[index].strftime('%Y-%m-%d')
        return data['date'][index] if isinstance(data['date'][index], str) else data['date'][index].strftime('%Y-%m-%d')

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
            'high': data['high'][index],
            'low': data['low'][index],
            'open': data['open'][index],
            'close': data['close'][index],
            'volume': data['volume'][index],
            'turnover': data['volume'][index] * data['low'][index],
            'turnover_rate': 0
        }

    def get_on_time_kl(self) -> Optional[Dict[str, Any]]:
        """获取实时K线数据"""
        try:
            # 构建新浪股票代码格式
            symbol = ""
            if self.code.startswith('US'):
                symbol = "gb_" + self.code[3:].lower()
            elif self.code.startswith('HK'):
                symbol = "hk" + self.code[3:]
            elif self.code.startswith('SZ'):
                symbol = "sz" + self.code[3:]
            elif self.code.startswith('SH'):
                symbol = "sh" + self.code[3:]
            else:
                return None
                
            try:
                # 获取A股实时数据
                if self.code.startswith('SZ') or self.code.startswith('SH'):
                    tickers = ak.stock_zh_a_spot_em()
                    for i in range(len(tickers)):
                        code = tickers['代码'][i]
                        match = False
                        
                        if self.code.startswith('SZ'):
                            match = code.startswith('0') or code.startswith('3')
                        elif self.code.startswith('SH'):
                            match = code.startswith('6') or code.startswith('7') or code.startswith('9')
                        
                        if match and self.code.endswith(code):
                            return {
                                'time_key': datetime.date.today(),
                                'high': tickers['最高'][i],
                                'low': tickers['最低'][i],
                                'open': tickers['今开'][i],
                                'close': tickers['最新价'][i],
                                'volume': tickers['成交量'][i],
                                'turnover': tickers['成交额'][i],
                                'turnover_rate': 0,
                                'id': 0
                            }
                return None
            except Exception as e:
                print(f"获取新浪实时数据失败: {e}")
                return None
        except Exception as e:
            print(f"获取新浪实时数据失败: {e}")
            return None

    def get_kline_data(self) -> pd.DataFrame:
        """获取历史K线数据"""
        # 如果没有提供日期范围，直接返回实时数据
        if self.start_date is None or self.end_date is None:
            return None
        data = None
        if self.code.startswith('US'):
            data = ak.stock_us_daily(symbol=self.code[3:], adjust="qfq")
            self.type = 1
        elif self.code.startswith('HK'):
            data = ak.stock_hk_daily(symbol=self.code[3:], adjust="qfq")
        elif self.code.startswith('SZ'):
            data = ak.stock_zh_a_daily(symbol='sz'+self.code[3:], end_date=self.end_date, adjust="qfq")
        elif self.code.startswith('SH'):
            data = ak.stock_zh_a_daily(symbol='sh'+self.code[3:], end_date=self.end_date, adjust="qfq")
        return data

    def get_kl(self) -> pd.DataFrame:
        """获取K线数据
        
        Returns:
            dict或DataFrame: K线数据
        """
        # 优先尝试获取实时数据
        if self.start_date is None or self.end_date is None:
            return self.get_on_time_kl()
        return self.get_kline_data()
