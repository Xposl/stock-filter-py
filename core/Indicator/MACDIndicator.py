from core.enum.indicator_group import IndicatorGroup
from core.utils import UtilsHelper

class MACDIndicator:
    difCount = 12
    dayCount = 26
    m = 9
    
    def __init__(self,difCount,dayCount,m):
        self.difCount = difCount
        self.dayCount = dayCount
        self.m = m

    def getKey(self):
        return 'MACD('+str(self.difCount)+','+str(self.dayCount)+')_indicator'
    
    def getGroup(self):
        return IndicatorGroup.POWER
    
    def calculate(self,klData):
        length = len(klData)
        closeData = []
        dif = []
        macd = []
        posData = []
        for klItem in klData:
            closeData.append(klItem['close'])
            
        emaS = UtilsHelper().EMA(closeData,self.difCount)
        emaL = UtilsHelper().EMA(closeData,self.dayCount)
        
        for i in range(length):
            dif.append(emaS[i] - emaL[i])
        
        emaDif =  UtilsHelper().EMA(dif,self.m)


        for i in range(length):
            macd.append((dif[i] - emaDif[i])*2)
            posData.append(1 if macd[i] > 0 else (-1 if macd[i] < 0 else 0))

        return {
            'posData': posData,
            'score': macd[length-1]
        }