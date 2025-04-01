from core.Enum.TickerKType import TickerKType
from core.API import APIHelper

from core.Strategy import Strategy,defaultStrategies

class TickerStrategy:
    updateTime = ''
    strategies = None
    APIHelper = APIHelper()

    def __init__(self,updateTime,strategies = None):
        self.updateTime = updateTime
        if strategies is not None:
            self.strategies = strategies

    def calculate(self,kLineData):
        return Strategy(self.strategies).calculate(kLineData)

    def updateTickerStrategy(self,ticker,kLineData):
        tickerId = ticker['id']
        length = len(kLineData)
        if length == 0:
            print('无数据')
            return
  
        strategies = self.calculate(kLineData)
        for strategyKey in strategies:
            result = strategies[strategyKey]
            self.APIHelper.tickerStrategy().updateItem(tickerId,strategyKey,TickerKType.DAY.value,self.updateTime,result)
        return strategies