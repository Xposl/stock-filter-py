"""
东方财富数据源K线数据处理模块
"""
import akshare as ak
import datetime
from typing import Dict, Any, Optional, Union
import pandas as pd

from . import KLineDataSource

class DongcaiKLineSource(KLineDataSource):
    """东方财富数据源K线数据处理类"""
    
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

    def get_data_time_key(self, data: Any, index: int) -> str:
        """获取数据时间键
        
        Args:
            data: K线数据
            index: 数据索引
            
        Returns:
            str: 时间键
        """
        return data['日期'][index]

    def convert_data(self, data: Any, index: int) -> Dict[str, Any]:
        """转换K线数据为统一格式
        
        Args:
            data: K线数据
            index: 数据索引
            
        Returns:
            dict: 标准格式的K线数据
        """
        return {
            'time_key': data['日期'][index],
            'high': data['最高'][index],
            'low': data['最低'][index],
            'open': data['开盘'][index],
            'close': data['收盘'][index],
            'volume': data['成交量'][index],
            'turnover': data['成交额'][index],
            'turnover_rate': data['换手率'][index]
        }

    def convert_on_time_data(self, data: Any, index: int) -> Dict[str, Any]:
        """转换实时数据为统一格式
        
        Args:
            data: 实时数据
            index: 数据索引
            
        Returns:
            dict: 标准格式的K线数据
        """
        return {
            'time_key': datetime.date.today(),
            'high': data['最高'][index],
            'low': data['最低'][index],
            'open': data['今开'][index],
            'close': data['最新价'][index],
            'volume': data['成交量'][index],
            'turnover': data['成交额'][index],
            'turnover_rate': 0
        }

    def convert_us_on_time_data(self, data: Any, index: int) -> Dict[str, Any]:
        """转换美股实时数据为统一格式
        
        Args:
            data: 实时数据
            index: 数据索引
            
        Returns:
            dict: 标准格式的K线数据
        """
        return {
            'time_key': datetime.date.today(),
            'high': data['最高价'][index],
            'low': data['最低价'][index],
            'open': data['开盘价'][index],
            'close': data['最新价'][index],
            'volume': 0,
            'turnover': 0,
            'turnover_rate': 0
        }

    def get_zh_on_time_data(self) -> Optional[Dict[str, Any]]:
        """获取中国A股实时数据"""
        tickers = ak.stock_zh_a_spot_em()
        for i in range(len(tickers)):
            code = tickers['代码'][i]
            if code.startswith('0') or code.startswith('3'):
                code = f'SZ.{str(code)}'
            elif code.startswith('6') or code.startswith('7') or code.startswith('9'):
                code = f'SH.{str(code)}'
            if code == self.code:
                return self.convert_on_time_data(tickers, i)
        return None

    def get_hk_on_time_data(self) -> Optional[Dict[str, Any]]:
        """获取港股实时数据"""
        tickers = ak.stock_hk_spot_em()
        for i in range(len(tickers)):
            code = f"HK.{tickers['代码'][i]}"
            if code == self.code:
                return self.convert_on_time_data(tickers, i)
        return None

    def get_us_on_time_data(self) -> Optional[Dict[str, Any]]:
        """获取美股实时数据"""
        tickers = ak.stock_us_spot_em()
        for i in range(len(tickers)):
            code = f"US.{tickers['代码'][i][4:]}"
            if code == self.code:
                return self.convert_us_on_time_data(tickers, i)
        return None

    def get_on_time_kl(self) -> Optional[Dict[str, Any]]:
        """获取实时K线数据"""
        data = None
        if self.code.startswith('US'):
            data = self.get_us_on_time_data()
        elif self.code.startswith('HK'):
            data = self.get_hk_on_time_data()
        elif self.code.startswith('SZ') or self.code.startswith('SH'):
            data = self.get_zh_on_time_data()
        
        if data is not None:
            data['id'] = 0
        return data

    def get_kl(self) -> Optional[Union[Dict[str, Any], pd.DataFrame]]:
        """获取K线数据"""
        # 如果没有提供日期范围，直接返回实时数据
        if self.start_date is None or self.end_date is None:
            return self.get_on_time_kl()
            
        data = None
        start = datetime.datetime.strptime(self.start_date, "%Y-%m-%d").strftime('%Y%m%d')
        end = datetime.datetime.strptime(self.end_date, "%Y-%m-%d").strftime('%Y%m%d')
        
        if self.code.startswith('US'):
            data = ak.stock_us_hist(symbol=f'105.{self.code[3:]}', start_date=start, end_date=end, adjust="qfq")
        elif self.code.startswith('HK'):
            data = ak.stock_hk_hist(symbol=self.code[3:], start_date=start, end_date=end, adjust="qfq")
        elif self.code.startswith('SZ') or self.code.startswith('SH'):
            data = ak.stock_zh_a_hist(symbol=self.code[3:], start_date=start, end_date=end, adjust="qfq")
            
        return data
