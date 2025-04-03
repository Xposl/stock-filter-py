from core.enum.ticker_k_type import TickerKType
from core.strategy import Strategy
from core.service.ticker_strategy_repository import TickerStrategyRepository

class TickerStrategy:
    updateTime = ''
    strategies = None

    def __init__(self,updateTime,strategies = None):
        self.updateTime = updateTime
        if strategies is not None:
            self.strategies = strategies

    def calculate(self,kLineData):
        return Strategy(self.strategies).calculate(kLineData)

    def update_ticker_strategy(self,ticker,kLineData):
        print('更新策略',ticker.code)
        length = len(kLineData)
        if length == 0:
            print('无数据')
            return
  
        strategies = self.calculate(kLineData)
        for strategyKey in strategies:
            result = strategies[strategyKey]
            TickerStrategyRepository().update_item(ticker.id,strategyKey,TickerKType.DAY.value,self.updateTime,result)
        return strategies
