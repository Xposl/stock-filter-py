from core.enum.indicator_group import IndicatorGroup
from core.utils.utils import UtilsHelper
import pandas as pd
from core.indicator.base_indicator import BaseIndicator

class WMSRIndicator(BaseIndicator):
    dayCount = 14
    
    def __init__(self,dayCount):
        self.dayCount = dayCount

    def getKey(self):
        return 'WMSR'+str(self.dayCount)+'_indicator'
    
    def getGroup(self):
        return IndicatorGroup.POWER
    
    def calculate(self,klData):
        length = len(klData)
        posData = []
        data = []
        Kline = pd.DataFrame(klData)
        lowestData = UtilsHelper().lowest(Kline['low'].values,self.dayCount)
        highestData = UtilsHelper().highest(Kline['high'].values,self.dayCount)
            
        for i in range(length):
            temp1 = highestData[i] - Kline['close'][i]
            temp2 = highestData[i] - lowestData[i]
            wr = -100 * temp1 / temp2 if temp2 > 0 else -100
            data.append(wr)
            status = 0
            if wr > -50:
                status = 1
            elif wr < -50:
                status = -1
            posData.append(status)
            
        
        return {
            'posData': posData,
            'score': data[length-1]
        }
