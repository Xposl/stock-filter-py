
from core.API import APIHelper

from core.Enum.TickerKType import TickerKType
from core.Filter import Filter
from core.utils import UtilsHelper

class TickerFilter:
    rule = None
    APIHelper = APIHelper()

    def __init__(self,rule = None):
        if rule is not None:
            self.rule = rule

    def run(self,tickers):
        result = []
        total = len(tickers)
        for i in range(total):
            ticker = tickers[i]
            UtilsHelper().runProcess(i,total,"recommend","[total:{total}]({id}){code}".format(
                id = ticker['id'],
                code = ticker['code'],
                total = len(result)
            ))
            
            kLineData = self.APIHelper.tickerDayLine().getItemsByTickerId(ticker['id'])
            strategyData = self.APIHelper.tickerStrategy().getItemsByTickerId(ticker['id'],TickerKType.DAY.value)
            indicatorData = self.APIHelper.tickerIndicator().getItemsByTickerId(ticker['id'],TickerKType.DAY.value)
            scoreData = self.APIHelper.tickerScore().getItemsByTickerId(ticker['id'])
            valuationData = self.APIHelper.tickerValuation().getItemsByTickerId(ticker['id'])
            filter = Filter(self.rule).calculate(ticker,kLineData,strategyData,indicatorData,scoreData,valuationData)
            if filter:
                print(ticker['code'] + ":"+ticker['name']+"\n")
                result.append(ticker)
        return result

