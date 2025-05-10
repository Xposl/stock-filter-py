"""
东方财富数据源股票获取模块
"""
from typing import List
import akshare as ak
import logging
from core.models.ticker import Ticker
from core.utils.retry_on_exception import retry_on_exception

logger = logging.getLogger(__name__)


class DongCaiTicker:
    """东方财富数据源股票获取类"""
    
    @retry_on_exception(max_retries=3, delay=5, backoff=2)
    def get_ch_tickers(self) -> List[Ticker]:
        """获取中国A股股票列表

        Returns:
            list: 包含所有A股股票信息的列表
        """
        result = []
        tickers = ak.stock_zh_a_spot_em()
        for i in range(len(tickers)):
            code:str = tickers['代码'][i]
            if code.startswith('0') or code.startswith('3'):
                code = f'SZ.{str(code)}'
            elif code.startswith('6') or code.startswith('7') or code.startswith('9'):
                code = f'SH.{str(code)}'
            elif code.startswith('83') or code.startswith('87') or code.startswith('88'):
                code = f'BJ.{str(code)}'
                # TODO: 跳过北交所
                continue
            else:
                continue

            result.append(Ticker(
                id=0,
                code=code,
                name=tickers['名称'][i],
                source=1
            ))
        return result

    @retry_on_exception(max_retries=3, delay=5, backoff=2)
    def get_hk_tickers(self) -> List[Ticker]:
        """获取香港股票列表

        Returns:
            list: 包含所有港股的列表
        """
        result = []
        tickers = ak.stock_hk_spot_em()
        for i in range(len(tickers)):
            if tickers['代码'][i][:2] not in ['00', '01', '02', '03', '06', '08', '09']:
                continue

            result.append(Ticker(
                id=0,
                code=f"HK.{tickers['代码'][i]}",
                name=tickers['名称'][i],
                source=1
            ))
        return result

    @retry_on_exception(max_retries=3, delay=5, backoff=2)
    def get_us_tickers(self) -> List[Ticker]:
        """获取美国股票列表

        Returns:
            list: 包含所有美股的列表
        """
        result = []
        tickers = ak.stock_us_spot_em()
        for i in range(len(tickers)):
            if '_' in tickers['代码'][i]:
                continue
        
            result.append(Ticker(
                id=0,
                code=f"US.{tickers['代码'][i][4:]}",
                name=tickers['名称'][i],
                source=1
            ))
        return result

    def get_tickers(self) -> List[Ticker]:
        """获取所有股票列表

        Returns:
            list: 包含所有股票的列表
        """
        result = []
        result.extend(self.get_hk_tickers())
        result.extend(self.get_ch_tickers())
        result.extend(self.get_us_tickers())
        return result
