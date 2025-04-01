from core.API import APIHelper

from core.Valuation import Valuation

class TickerValuation:
    updateTime = ''
    valuations = None
    APIHelper = APIHelper()

    def __init__(self,updateTime,valuations = None):
        self.updateTime = updateTime
        if valuations is not None:
            self.valuations = valuations

    def calculate(self,ticker):
        return Valuation(self.updateTime,self.valuations).calculate(ticker)

    def updateTickerValuation(self,ticker):
        tickerId = ticker['id']
        valuations = self.calculate(ticker)
        for valuationKey in valuations:
            result = valuations[valuationKey]
            if result is not None:
                self.APIHelper.tickerValuation().updateItem(tickerId,valuationKey,self.updateTime,result)
        return valuations
