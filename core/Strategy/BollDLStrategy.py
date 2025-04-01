# BollDLStrategy.py
from core.utils import UtilsHelper

class BollDLStrategy:
    dayCount = 21
    multi = 2

    def getKey(self):
        return 'BOLL_DL_strategy'

    def calculate(self,klData):
        lossData = []
        closeData = []

        for klItem in klData:
            closeData.append(klItem['close'])

        smaData = UtilsHelper().SMA(closeData,self.dayCount)
        devData = UtilsHelper().STDDEV(closeData,self.dayCount)

        for devItem in devData:
            lossData.append(devItem * self.multi)

        return UtilsHelper().doubleLinePos(closeData,smaData,devData)

        