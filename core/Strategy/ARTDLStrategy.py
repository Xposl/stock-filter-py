# ARTsmStrategy.py
from core.utils import UtilsHelper

class ARTDLStrategy:
    dayCount = 21
    multi = 6.3

    def getKey(self):
        return 'ART_DL_strategy'

    def calculate(self,klData):
        artData = UtilsHelper().RATR(klData,self.dayCount)
        lossData = []
        closeData = []

        for klItem in klData:
            closeData.append(klItem['close'])

        for artItem in artData:
            lossData.append(artItem * self.multi)

        return UtilsHelper().doubleLinePos(closeData,closeData,lossData)

        