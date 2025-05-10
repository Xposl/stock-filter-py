"""
东方财富数据源K线数据处理模块
"""
import math
import akshare as ak
import datetime
from typing import List, Optional

from core.schema.k_line import KLine

from .base_source import BaseSource

class DongcaiKLineSource(BaseSource):
    """东方财富数据源K线数据处理类"""

    def _get_zh_data_on_time(self, code: str) -> Optional[KLine]:
        """获取中国A股实时数据"""
        tickers = ak.stock_zh_a_spot_em()
        for i in range(len(tickers)):
            ticker_code:str = tickers['代码'][i]
            if ticker_code.startswith('0') or ticker_code.startswith('3'):
                ticker_code = f'SZ.{str(ticker_code)}'
            elif ticker_code.startswith('6') or ticker_code.startswith('7') or ticker_code.startswith('9'):
                ticker_code = f'SH.{str(ticker_code)}'
            if ticker_code == code:
                return KLine(
                    time_key=datetime.date.today().strftime('%Y-%m-%d'),
                    high=tickers['最高'][i],
                    low=tickers['最低'][i],
                    open=tickers['今开'][i],
                    close=tickers['最新价'][i],
                    volume= tickers['成交量'][i],
                    turnover= tickers['成交额'][i],
                    turnover_rate= tickers['换手率'][i]
                )
        return None

    def _get_hk_data_on_time(self, code: str) -> Optional[KLine]:
        """获取港股实时数据"""
        tickers = ak.stock_hk_spot_em()
        for i in range(len(tickers)):
            ticker_code = f"HK.{tickers['代码'][i]}"
            if ticker_code == code:
                return KLine(
                    time_key=datetime.date.today().strftime('%Y-%m-%d'),
                    high=tickers['最高'][i],
                    low=tickers['最低'][i],
                    open=tickers['今开'][i],
                    close=tickers['最新价'][i],
                    volume= tickers['成交量'][i],
                    turnover= tickers['成交额'][i],
                    turnover_rate= 0
                )
        return None

    def _get_us_data_on_time(self, code: str) -> Optional[KLine]:
        """获取美股实时数据"""
        tickers = ak.stock_us_spot_em()
        for i in range(len(tickers)):
            ticker_code = f"US.{tickers['代码'][i][4:]}"
            if ticker_code == code:
                return KLine(
                    time_key=datetime.date.today().strftime('%Y-%m-%d'),
                    high=tickers['最高价'][i],
                    low=tickers['最低价'][i],
                    open=tickers['开盘价'][i],
                    close=tickers['最新价'][i],
                    volume= tickers['成交量'][i],
                    turnover= tickers['成交额'][i],
                    turnover_rate= tickers['换手率'][i]
                )
        return None

    def get_kl_on_time(self, code: str) -> Optional[KLine]:
        """获取实时K线数据"""
        data = None
        if code.startswith('US'):
            data = self._get_us_data_on_time()
        elif code.startswith('HK'):
            data = self._get_hk_data_on_time()
        elif code.startswith('SZ') or code.startswith('SH'):
            data = self._get_zh_data_on_time()
        return data

    def get_kl(self, code: str, start_date: str, end_date: Optional[str]=None) -> List[KLine]:
        """获取K线数据"""
            
        data = None
        start = datetime.datetime.strptime(start_date, "%Y-%m-%d").strftime('%Y%m%d')
        end = datetime.datetime.strptime(end_date, "%Y-%m-%d").strftime('%Y%m%d') if end_date is not None else datetime.date.today().strftime('%Y%m%d')
        
        if code.startswith('US'):
            data = ak.stock_us_hist(symbol=f'105.{code[3:]}', start_date=start, end_date=end, adjust="qfq")
        elif code.startswith('HK'):
            data = ak.stock_hk_hist(symbol=code[3:], start_date=start, end_date=end, adjust="qfq")
        elif code.startswith('SZ') or code.startswith('SH'):
            data = ak.stock_zh_a_hist(symbol=code[3:], start_date=start, end_date=end, adjust="qfq")
            
        if data is not None:
            return [KLine(
                time_key= data['日期'][index].strftime('%Y-%m-%d') if isinstance(data['日期'][index],datetime.date) else data['日期'][index],
                high=data['最高'][index],
                low=data['最低'][index],
                open=data['开盘'][index],
                close=data['收盘'][index],
                volume=data['成交量'][index],
                turnover=0 if math.isnan(data['成交额'][index]) else data['成交额'][index],
                turnover_rate=0 if math.isnan(data['换手率'][index]) else data['换手率'][index]
            ) for index in range(len(data))]
        return None
