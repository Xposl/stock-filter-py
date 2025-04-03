from core.enum.ticker_k_type import TickerKType
from core.service.ticker_indicator_repository import TickerIndicatorRepository

from core.Indicator import Indicator

class TickerIndicator:
    updateTime = ''
    indicators = None

    def __init__(self,updateTime,indicators = None):
        self.updateTime = updateTime
        if indicators is not None:
            self.indicators = indicators

    def calculate(self,kLineData):
        return Indicator(self.indicators).calculate(kLineData)

    def update_ticker_indicator(self,ticker,kLineData):
        length = len(kLineData)
        if length == 0:
            print('无数据')
            return

        indicators = self.calculate(kLineData)
        for indicatorKey in indicators:
            result = indicators[indicatorKey]
            TickerIndicatorRepository().update_item(ticker.id, indicatorKey, TickerKType.DAY.value, self.updateTime, result)
        return indicators
