from core.utils import UtilsHelper

class MABaseStrategy:
    p1 = 13
    p2 = 21
    p3 = 55

    def getKey(self):
        return 'MA_Base_strategy'
    
    def calculate(self,klData):
        length = len(klData)
        closeData = []
        posData = []
        for klItem in klData:
            closeData.append(klItem['close'])
            
        maM = UtilsHelper().EMA(closeData,self.p2)
        maL = UtilsHelper().EMA(closeData,self.p3)
        
        status = 0
        for i in range(length):
            if i < 2:
                posData.append(0)
                continue
            close = closeData[i]
            slow_base = closeData[i - self.p1] if i - self.p1 > 0 else closeData[0]
            
            diff = (maL[i] - maL[i-1])/maL[i] if maL[i] > 0 else 0

            if diff > - 0.001 and maM[i-1] < maM[i] and close > slow_base:
                status = 1
            
            if diff < 0.001 and maM[i-1] > maM[i] and close <= slow_base:
                status = -1
            posData.append(status)
        
        return posData
