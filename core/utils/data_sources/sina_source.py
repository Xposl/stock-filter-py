"""
新浪数据源K线数据处理模块
"""
import akshare as ak
import datetime
from typing import Dict, Any, List, Optional
import pandas as pd

from core.schema.k_line import KLine

from .base_source import BaseSource

class SinaKLineSource(BaseSource):
    """新浪数据源K线数据处理类"""

    def get_kl_on_time(self, code: str) -> Optional[KLine]:
        """获取实时K线数据
        
        Returns:
            KLine: 实时K线数据，失败返回None
        """
        try:
            # 获取A股实时数据
            if code.startswith('SZ') or code.startswith('SH'):
                tickers = ak.stock_zh_a_spot_em()
                for i in range(len(tickers)):
                    ticker_code = tickers['代码'][i]
                    match = False
                    if code.startswith('SZ'):
                        match = ticker_code.startswith('0') or ticker_code.startswith('3')
                    elif code.startswith('SH'):
                        match = ticker_code.startswith('6') or ticker_code.startswith('7') or ticker_code.startswith('9')
                    
                    if match and ticker_code.endswith(code):
                        return KLine(
                            time_key=datetime.date.today().strftime('%Y-%m-%d'),
                            high=tickers['最高'][i],
                            low=tickers['最低'][i],
                            open=tickers['今开'][i],
                            close=tickers['最新价'][i],
                            volume=tickers['成交量'][i],
                            turnover=tickers['成交额'][i],
                            turnover_rate=0,
                        )
            return None
        except Exception as e:
            print(f"获取新浪实时数据失败: {e}")
            return None

    def get_kl(self, code:str, start_date: str, end_date: Optional[str]=None) -> List[KLine]:
        """获取K线数据
        
        Returns:
            List[KLine]: K线数据列表，失败返回None
        """
        data = None
        type = 0
        if code.startswith('US'):
            data = ak.stock_us_daily(symbol=code[3:], adjust="qfq")
            type = 1
        elif code.startswith('HK'):
            data = ak.stock_hk_daily(symbol=code[3:], adjust="qfq")
        elif code.startswith('SZ'):
            data = ak.stock_zh_a_daily(symbol='sz'+code[3:], start_date=start_date, end_date=end_date, adjust="qfq")
        elif code.startswith('SH'):
            data = ak.stock_zh_a_daily(symbol='sh'+code[3:], start_date=start_date, end_date=end_date, adjust="qfq")

        if data is not None:
            if type == 1:
                return [KLine(
                    time_key= data.index[index].strftime('%Y-%m-%d'),
                    high= data['high'][index],
                    low= data['low'][index],
                    open= data['open'][index],
                    close= data['close'][index],
                    volume= data['volume'][index],
                    turnover= data['volume'][index] * data['low'][index],
                    turnover_rate= 0
                ) for index in range(len(data))]
            return [KLine(
                time_key= data['date'][index] if isinstance(data['date'][index], str) else data['date'][index].strftime('%Y-%m-%d'),
                high= data['high'][index],
                low= data['low'][index],
                open= data['open'][index],
                close= data['close'][index],
                volume= data['volume'][index],
                turnover= data['volume'][index] * data['low'][index],
                turnover_rate= 0
            ) for index in range(len(data))]
        return None
