from typing import Any, Dict, Optional
from core.enum.indicator_group import IndicatorGroup
from core.utils import UtilsHelper

class BullBearPowerIndicator:
    dayCount = 50
    atrDay = 5

    def getKey(self) -> str:
        return 'BUll_BEAR_POWER_indicator'

    def getGroup(self) -> IndicatorGroup:
        return IndicatorGroup.POWER
    
    def calculate(self,klData: Optional[list]=None) -> Dict[str, Any]:
        """
        计算指标
        """
        length = len(klData)
        closeData = []
        highData = []
        lowData = []
        posData = []
        for klItem in klData:
            highData.append(klItem['high'])
            lowData.append(klItem['low'])
            closeData.append(klItem['close'])
        
        atrData = UtilsHelper().RATR(klData,self.atrDay)
        lowestData = UtilsHelper().LOWEST(lowData,self.dayCount)
        highestData = UtilsHelper().HIGHEST(highData,self.dayCount)
        
        score = 0
        for i in range(length):
            bullTrend = (closeData[i] - lowestData[i])/atrData[i] if atrData[i] > 0 else 0
            bearTrend = (highestData[i] - closeData[i])/atrData[i] if atrData[i] > 0 else 0
            score = bullTrend - bearTrend
            posData.append(1 if score > 0 else (-1 if score < 0 else 0))
        return {
            'posData': posData,
            'score': score
        }
