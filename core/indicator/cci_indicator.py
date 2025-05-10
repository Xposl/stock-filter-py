from core.enum.indicator_group import IndicatorGroup
from core.utils.utils import UtilsHelper

class CCIIndicator:
    dayCount = 0
    
    def __init__(self,dayCount):
        self.dayCount = dayCount

    def getKey(self):
        return 'CCI'+str(self.dayCount)+'_indicator'

    def getGroup(self):
        return IndicatorGroup.POWER
    
    def calculate(self,klData):
        length = len(klData)
        posData = []
 
        cci = UtilsHelper().CCI(klData,self.dayCount)
        
        for i in range(length):
            if i < 2:
                posData.append(0)
                continue
            status = 0
            if (cci[i-1] < -100 and cci[i] >= -100) or (cci[i-1] < 0 and cci[i] >= 0) or (cci[i-1] < 100 and cci[i] >= 100):
                status = 1
            elif (cci[i-1] > -100 and cci[i] <= -100) or (cci[i-1] > 0 and cci[i] <= 0) or (cci[i-1] > 100 and cci[i] <= 100):
                status = -1
            else:
                status = posData[i-1]
            posData.append(status)

        return {
            'posData': posData,
            'score': cci[length-1]
        }
