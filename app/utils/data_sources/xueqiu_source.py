"""
雪球数据源K线数据处理模块
"""
import datetime
import math
from typing import Optional

from core.enum.ticker_type import TickerType
from core.models.ticker import dict_to_ticker

from ..xueqiu.xueqiu_api import XueqiuApi
from .base_source import BaseSource, KLine


class XueqiuKLineSource(BaseSource):
    """雪球数据源K线数据处理类"""

    def __init__(self):
        self.xueqiu = XueqiuApi()

    def get_on_time_kl(self, code: str) -> Optional[KLine]:
        """获取实时K线数据

        Returns:
            KLine: 实时K线数据，失败返回None
        """
        try:
            stock_code = ""
            if code.startswith("US") or code.startswith("HK"):
                stock_code = code[3:]
            elif code.startswith("SZ"):
                stock_code = "SZ" + code[3:]
            elif code.startswith("SH"):
                stock_code = "SH" + code[3:]

            quote = self.xueqiu.get_stock_quote(stock_code)
            if quote:
                return KLine(
                    time_key=datetime.date.today().strftime("%Y-%m-%d"),
                    high=quote.quote.high,
                    low=quote.quote.low,
                    open=quote.quote.open,
                    close=quote.quote.current,
                    volume=quote.quote.volume,
                    turnover=quote.quote.amount,
                    turnover_rate=quote.quote.turnover_rate,
                )
            return None
        except Exception as e:
            print(f"获取雪球实时数据失败: {e}")
            return None

    def get_kl(
        self, code: str, start_date: str, end_date: Optional[str] = None
    ) -> list[KLine]:
        """获取K线数据

        Returns:
            List[KLine]: K线数据列表，失败返回None
        """
        if start_date is not None:
            if code.startswith("US") or code.startswith("HK"):
                data = self.xueqiu.get_stock_history(code[3:], start_date)
            elif self.code.startswith("SZ"):
                data = self.xueqiu.get_stock_history("SZ" + code[3:], start_date)
            elif self.code.startswith("SH"):
                data = self.xueqiu.get_stock_history("SH" + code[3:], start_date)

        if data is not None:
            return [
                KLine(
                    time_key=datetime.datetime.fromtimestamp(
                        data["日期"][index] / 1000
                    ).strftime("%Y-%m-%d"),
                    high=data["最高"][index],
                    low=data["最低"][index],
                    open=data["开盘"][index],
                    close=data["收盘"][index],
                    volume=data["成交量"][index],
                    turnover=0
                    if math.isnan(data["成交额"][index])
                    else data["成交额"][index],
                    turnover_rate=0
                    if math.isnan(data["换手率"][index])
                    else data["换手率"][index],
                )
                for index in range(len(data))
            ]
        return None


class XueqiuTicker:
    type = {
        0: TickerType.STOCK,
        4: TickerType.ETF,
        5: TickerType.STOCK,
        6: TickerType.STOCK,
        11: TickerType.STOCK,
        30: TickerType.STOCK,
        32: TickerType.WARRANT,
        33: TickerType.ETF,
        34: TickerType.BOND,
        82: TickerType.STOCK,
    }

    status = {
        0: 0,  # 未上市
        1: 1,  # 正常
        2: 0,  # 停牌
        3: 0,  # 退市
    }

    def __init__(self):
        self.api = XueqiuApi()

    def get_ticker(self, code, name):
        ticker = dict_to_ticker({"id": 0, "code": code, "name": name})

        if ticker is not None:
            quote = self.api.get_stock_quote(code)
            if quote is None:
                ticker.type = TickerType.DEL.value
                ticker.is_deleted = True
                ticker.status = 0
                return ticker

            if quote.quote.status in self.status:
                if quote.quote.status == 0 or quote.quote.status == 3:
                    ticker.is_deleted = True
                ticker.status = (
                    self.status[quote.quote.status]
                    if quote.quote.open is not None
                    else 0
                )
            else:
                raise Exception("Unknown status", quote.quote.status)

            if quote.quote.type in self.type:
                if quote.quote.type == 32:
                    ticker.status = 0
                ticker.type = self.type[quote.quote.type].value
            else:
                raise Exception("Unknown Type", quote.quote.type)

            ticker.lot_size = (
                quote.quote.lot_size if quote.quote.lot_size is not None else -1
            )
            ticker.pe_forecast = (
                quote.quote.pe_forecast if quote.quote.pe_forecast is not None else -1
            )
            ticker.pettm = quote.quote.pe_ttm if quote.quote.pe_ttm is not None else -1
            ticker.pb = quote.quote.pb if quote.quote.pb is not None else -1
            ticker.total_share = (
                quote.quote.total_shares if quote.quote.total_shares is not None else -1
            )
        return ticker
