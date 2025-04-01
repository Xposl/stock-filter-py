from core.Enum.IndicatorGroup import IndicatorGroup
from core.utils import UtilsHelper

class KDJIndicator:
    P1 = 9
    P2 = 3
    P3 = 3

    def getKey(self):
        return 'KDJ_indicator'

    def getGroup(self):
        return IndicatorGroup.POWER
    
    def calculate(self,klData):
        length = len(klData)
        closeData = []
        highData = []
        lowData = []
        rsvData = []
        jData = []
        posData = []
        for klItem in klData:
            highData.append(klItem['high'])
            lowData.append(klItem['low'])
            closeData.append(klItem['close'])

        lowestData = UtilsHelper().LOWEST(lowData,self.P1)
        highestData = UtilsHelper().HIGHEST(highData,self.P1)

        for i in range(length):
            divid = highestData[i]-lowestData[i]
            rsv = (closeData[i] - lowestData[i])/divid if divid > 0 else 0
            rsv = rsv * 100
            rsvData.append(rsv)
            
        kData = UtilsHelper().MA(rsvData,self.P2,1)
        dData = UtilsHelper().MA(kData,self.P3,1)
 
        for i in range(length):
            jValue = 3 * kData[i] - 2 * dData[i]
            jData.append(jValue)

            if i < 2:
                posData.append(0)
                continue

            if jValue > 100 and kData[i] > 90 and dData[i] > 80:
                posData.append(-1)
            elif jValue < 0 and kData[i] < 10 and dData[i] < 20:
                posData.append(1)
            elif jValue > kData[i]:
                posData.append(1)
            elif jValue < kData[i]:
                posData.append(-1)
            else:
                posData.append(0)
        
        return {
            'posData': posData,
            'score': jData[length-1]
        }
