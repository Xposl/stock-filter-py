
from core.API import APIHelper

from core.Score import Score

class TickerScore:
    rule = None
    APIHelper = APIHelper()

    def __init__(self,rule = None):
        if rule is not None:
            self.rule = rule

    def calculate(self,ticker,kLineData,strategyData,indicatorData,valuationData):
        return Score(self.rule).calculate(ticker,kLineData,strategyData,indicatorData,valuationData)

    def updateTickerScore(self,ticker,kLineData,strategyData,indicatorData,valuationData):
        result = self.calculate(ticker,kLineData,strategyData,indicatorData,valuationData)
        self.APIHelper.tickerScore().updateItems(ticker['id'],result)

