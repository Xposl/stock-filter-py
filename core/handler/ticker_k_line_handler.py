"""
股票K线数据处理模块
"""
from typing import List, Optional, Dict, Any

from core.enum.ticker_type import TickerType
from core.schema.k_line import KLine
from core.utils.data_sources import (
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

    def get_kl_on_time(self, code: str, source: int) -> Optional[KLine]:
        """获取最新K线数据
        
        Args:
            code: 股票代码
            source: 数据源 1=东财 2=新浪 3=雪球
            
        Returns:
            KLine: 最新的K线数据，失败返回None
        """
        try:
            # 根据参数创建数据源
            if source == 1:
                data_source = DongcaiKLineSource()
            elif source == 2:
                data_source = SinaKLineSource()
            elif source == 3:
                data_source = XueqiuKLineSource()
            else:
                print(f"未知数据源: {source}")
                return None
            
            # 获取实时数据
            data = data_source.get_kl_on_time(code)
            # 数据获取失败，尝试使用东财数据源作为备选
            if data is None and source != 1:
                return DongcaiKLineSource().get_kl_on_time(code)
                
            return None
        except Exception as e:
            print(f"获取实时K线数据失败: {e}")
            return None

    def get_kl(self, code: str, source: int, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Optional[List[KLine]]:
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
            data_source = DongcaiKLineSource()
        elif source == 2:
            data_source = SinaKLineSource()
        elif source == 3:
            data_source = XueqiuKLineSource()
        else:
            print(f"未知数据源: {source}")
            return None
 
        # 获取K线数据
        data = data_source.get_kl(code, start_date, end_date)
        if data is None:
            print(f'数据失效 source:{source}')
            return None
        
        # 处理历史数据
        result = []
        for i in range(len(data)):
            if data[i].time_key >= start_date and data[i].time_key <= end_date:
                result.append(data[i])
        return result