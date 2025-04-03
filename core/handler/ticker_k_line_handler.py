"""
股票K线数据处理模块
"""
import datetime
from typing import Optional, Dict, Any, Union
import pandas as pd

from core.enum.ticker_type import TickerType
from .data_sources import (
    DongcaiKLineSource,
    SinaKLineSource,
    XueqiuKLineSource
)

class TickerKLineHandler:
    """股票K线数据工具类"""

    TICKER_TYPES = [
        TickerType.STOCK,
        TickerType.IDX,
        TickerType.ETF,
        TickerType.PLATE
    ]

    def get_history_kl(self, code: str, source: int, start_date: Optional[str] = None, 
                      end_date: Optional[str] = None) -> Optional[list]:
        """获取历史K线数据
        
        Args:
            code: 股票代码
            source: 数据源 1=东财 2=新浪 3=雪球
            start_date: 开始日期，格式为'YYYY-MM-DD'
            end_date: 结束日期，格式为'YYYY-MM-DD'
            
        Returns:
            list: K线数据列表，失败返回None
        """
        if not start_date or not end_date:
            print('获取历史数据需要提供开始和结束日期')
            return None
        
        # 根据参数创建数据源
        if source == 1:
            data_source = DongcaiKLineSource(code, start_date, end_date)
        elif source == 2:
            data_source = SinaKLineSource(code, start_date, end_date)
        elif source == 3:
            data_source = XueqiuKLineSource(code, start_date, end_date)
        else:
            print(f"未知数据源: {source}")
            return None
 
        # 获取K线数据
        result = []
        data = data_source.get_kl()
        if data is None:
            print(f'数据失效 source:{source}')
            return None
        
        # 如果返回的是实时数据（一个dict而不是dataframe）
        if isinstance(data, dict):
            return [data]
        
        # 处理历史数据
        for i in range(len(data)):
            time_key = data_source.get_data_time_key(data, i)
            # 确保类型一致，将time_key作为字符串与字符串日期比较
            if isinstance(time_key, datetime.date):
                time_key_str = time_key.strftime('%Y-%m-%d')
            else:
                time_key_str = str(time_key)
                
            if time_key_str >= start_date and time_key_str <= end_date:
                result.append(data_source.convert_data(data, i))
        return result

    def get_kl(self, code: str, source: int) -> Optional[Dict[str, Any]]:
        """获取最新K线数据
        
        Args:
            code: 股票代码
            source: 数据源 1=东财 2=新浪 3=雪球
            
        Returns:
            dict: 最新的K线数据，失败返回None
        """
        try:
            # 根据参数创建数据源
            if source == 1:
                data_source = DongcaiKLineSource(code)
            elif source == 2:
                data_source = SinaKLineSource(code)
            elif source == 3:
                data_source = XueqiuKLineSource(code)
            else:
                print(f"未知数据源: {source}")
                return None
            
            # 获取实时数据
            data = data_source.get_kl()
            
            # 如果是字典类型的数据（单条数据），直接返回
            if isinstance(data, dict):
                return data
                
            # 如果是DataFrame类型的数据，获取最后一条
            if data is not None and len(data) > 0:
                return data_source.convert_data(data, len(data) - 1)
                    
            # 数据获取失败，尝试使用东财数据源作为备选
            if source != 1:
                return DongcaiKLineSource(code).get_on_time_kl()
                
            return None
        except Exception as e:
            print(f"获取实时K线数据失败: {e}")
            # 出错时尝试使用东财数据源作为备选
            if source != 1:
                try:
                    return DongcaiKLineSource(code).get_on_time_kl()
                except:
                    pass
            return None
