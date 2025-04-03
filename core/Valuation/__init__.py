from core.service.ticker_valuation_repository import TickerValuationRepository
from .investorsobserver_valuation import InvestorsobserverValuation

defaultValuations = [
   InvestorsobserverValuation()
]

class Valuation:
    group = []
    groupMap = {}
    updateTime = ''

    def __init__(self,updateTime,group=None):
        if group is not None:
            self.group = group
        else:
            self.group = defaultValuations
        for item in self.group:
            self.groupMap[item.getKey()] = item
        self.updateTime = updateTime

    def calculate(self,ticker):
        result = {}
        for item in self.group:
            res = self.calculateByKey(item.getKey(),ticker)
            result[item.getKey()] = res
        return result


    def calculateByKey(self,valuationKey,ticker):
        if self.groupMap[valuationKey] is None:
            print('error，找不到估值模型',valuationKey)
            return

        existItem = TickerValuationRepository().get_item_by_ticker_id_and_key(ticker.id,valuationKey)
        if existItem is None or existItem.time_key < self.updateTime:
            return self.groupMap[valuationKey].calculate(ticker)
        return existItem
