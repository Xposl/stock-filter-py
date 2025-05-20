"""
股票K线数据处理模块
"""
from typing import List, Optional, Dict, Any
import time
from threading import Lock

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

    # K线缓存，key为(code, source, start_date, end_date)
    # Kline cache, key: (code, source, start_date, end_date)
    _kl_cache: Dict = {}
    _kl_cache_lock = Lock()

    def get_kl_on_time(self, code: str, source: int) -> (Optional[KLine], Optional[int]):
        """获取最新K线数据，返回(数据, 实际用的source)"""
        try:
            tried = set()
            for i in range(3):
                s = (source + i - 1) % 3 + 1  # 1,2,3循环
                if s in tried:
                    continue
                tried.add(s)
                try:
                    if s == 1:
                        data_source = DongcaiKLineSource()
                    elif s == 2:
                        data_source = SinaKLineSource()
                    elif s == 3:
                        data_source = XueqiuKLineSource()
                    else:
                        continue
                    data = data_source.get_kl_on_time(code)
                    if data is not None:
                        return data, s
                except Exception as e:
                    print(f"源{s}获取实时K线异常: {e}")
                    continue
            return None, None
        except Exception as e:
            print(f"获取实时K线数据失败: {e}")
            return None, None

    def get_kl(self, code: str, source: int, start_date: Optional[str] = None, end_date: Optional[str] = None) -> (Optional[List[KLine]], Optional[int]):
        """获取历史K线数据，返回(数据, 实际用的source)，5分钟内缓存"""
        if not start_date or not end_date:
            print('获取历史数据需要提供开始和结束日期')
            return None, None
        cache_key = (code, source, start_date, end_date)
        now = time.time()
        with self._kl_cache_lock:
            cache_entry = self._kl_cache.get(cache_key)
            if cache_entry:
                print(f'缓存命中 code:{code} source:{source} start_date:{start_date} end_date:{end_date}')
                data, used_source, ts = cache_entry
                if now - ts < 300:  # 5分钟=300秒
                    return data, used_source
        tried = set()
        for i in range(3):
            s = (source + i - 1) % 3 + 1  # 1,2,3循环
            if s in tried:
                continue
            tried.add(s)
            try:
                if s == 1:
                    data_source = DongcaiKLineSource()
                elif s == 2:
                    data_source = SinaKLineSource()
                elif s == 3:
                    data_source = XueqiuKLineSource()
                else:
                    continue
                data = data_source.get_kl(code, start_date, end_date)
                if data is not None and len(data) > 0:
                    # 处理历史数据
                    result = []
                    for i in range(len(data)):
                        if data[i].time_key >= start_date and data[i].time_key <= end_date:
                            result.append(data[i])
                    if len(result) > 0:
                        with self._kl_cache_lock:
                            self._kl_cache[cache_key] = (result, s, now)
                        return result, s
            except Exception as e:
                print(f"源{s}获取历史K线异常: {e}")
                continue
        print(f'所有数据源均无数据 code:{code}')
        return None, None