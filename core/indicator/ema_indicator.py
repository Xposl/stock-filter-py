from typing import List
from core.enum.indicator_group import IndicatorGroup
from core.schema.k_line import KLine
from core.utils.utils import UtilsHelper
from core.indicator.base_indicator import BaseIndicator

class EMAIndicator(BaseIndicator):
    dayCount = 0
    
    def __init__(self,dayCount):
        self.dayCount = dayCount

    def getKey(self):
        return 'EMA'+str(self.dayCount)+'_indicator'
    
    def getGroup(self):
        return IndicatorGroup.BASE
    
    def calculate(self,klData: List[KLine]):
        length = len(klData)
        closeData = []
        posData = []
        for klItem in klData:
            closeData.append(klItem.close)
            
        ma = UtilsHelper().ema(closeData,self.dayCount)
        for i in range(length):
            if i < 2:
                posData.append(0)
                continue
            close = closeData[i]
            posData.append(1 if close > ma[i] else (-1 if close < ma[i] else 0))
        
        return {
            'posData': posData,
            'score': ma[length-1]
        }
