from core.enum.indicator_group import IndicatorGroup
from core.utils.utils import UtilsHelper
import pandas as pd
from core.indicator.base_indicator import BaseIndicator

class RSIIndicator(BaseIndicator):
    dayCount = 14

    def getKey(self):
        return 'RSI_indicator'

    def getGroup(self):
        return IndicatorGroup.POWER
    
    def calculate(self,klData):
        length = len(klData)
        posData = []
        upTemp = []
        downTemp = []
        rsiData = []
        Kline = pd.DataFrame(klData)

        for i in range(length):
            if i < 1:
                upTemp.append(0)
                downTemp.append(0)
                continue
            close = Kline['close'][i]
            lastClose = Kline['close'][i-1]
            upTemp.append(max(close - lastClose,0))
            downTemp.append(abs(close - lastClose))
        
        maUP = UtilsHelper().ma(upTemp,self.dayCount,1)
        maDown = UtilsHelper().ma(downTemp,self.dayCount,1)
        for i in range(length):
            if i < 1:
                posData.append(0)
                rsiData.append(0)
                continue
            rsi = (maUP[i] / maDown[i]) * 100 if maDown[i] > 0 else 100
            rsiData.append(rsi)
            if rsi > 80:
                posData.append(-1)
            elif rsi >50:
                posData.append(1)
            elif rsi > 20:
                posData.append(-1)
            else:
                posData.append(1)
        
        return {
            'posData': posData,
            'score': rsiData[length-1]
        }
