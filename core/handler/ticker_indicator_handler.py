from typing import Optional

from core.enum.ticker_k_type import TickerKType
from core.indicator import Indicator
from core.models.ticker import Ticker
from core.repository.ticker_indicator_repository import TickerIndicatorRepository


class TickerIndicatorHandler:
    updateTime = ""
    indicators = None

    def __init__(self, updateTime: str, indicators: Optional[list] = None):
        self.updateTime = updateTime
        if indicators is not None:
            self.indicators = indicators

    def calculate(self, kLineData: Optional[list] = None):
        """
        计算指标
        """
        return Indicator(self.indicators).calculate(kLineData)

    def update_ticker_indicator(self, ticker: Ticker, kLineData: Optional[list] = None):
        """
        更新指标
        """
        length = len(kLineData)
        if length == 0:
            print("无数据")
            return

        indicators = self.calculate(kLineData)
        for indicatorKey in indicators:
            result = indicators[indicatorKey]
            TickerIndicatorRepository().update_item(
                ticker.id, indicatorKey, TickerKType.DAY.value, self.updateTime, result
            )
        return indicators
