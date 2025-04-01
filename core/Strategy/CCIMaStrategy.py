from core.utils import UtilsHelper

class CCIMaStrategy:
    cciSLen = 13
    cciMLen = 21
    cciLLen = 34
    dayWait = 2

    def getParams(self):
        return {
            'cciSLen': self.cciSLen,
            'cciMLen': self.cciMLen,
            'cciLLen': self.cciLLen,
            'dayWait': self.dayWait
        }

    def setParams(self,param):
        self.cciSLen = param['cciSLen'] if 'cciSLen' in param else self.cciSLen
        self.cciMLen = param['cciMLen'] if 'cciMLen' in param else self.cciMLen
        self.cciLLen = param['cciLLen'] if 'cciLLen' in param else self.cciLLen
        self.dayWait = param['dayWait'] if 'dayWait' in param else self.dayWait

    def getKey(self):
        return 'CCI_MA_strategy'
    
    def calculate(self,klData):
        length = len(klData)
        closeData = []
        posData = []
        for klItem in klData:
            closeData.append(klItem['close'])
        cciS = UtilsHelper().CCI(klData,self.cciSLen)
        cciM = UtilsHelper().CCI(klData,self.cciMLen)
        cciL = UtilsHelper().CCI(klData,self.cciLLen)

        maL = UtilsHelper().HMA(closeData,self.cciLLen)
        
        condiData = []
        v2Data = []
        status = 0
        for i in range(length):
            cciTS = UtilsHelper().keepUpTrend(cciS,0,i,2)
            cciTM = UtilsHelper().keepUpTrend(cciM,0,i,2)
            cciTL = UtilsHelper().keepUpTrend(cciL,0,i,2)
            ## 逻辑测试
            v1 = cciS[i] if cciTS else cciS[i] - 100
            v2 = cciM[i] if cciTM else v1
            condi = cciL[i] if cciTL else v2
            v2Data.append(v2)
            condiData.append(condi)

            if i < self.cciSLen:
                posData.append(0)
                continue

            buy = UtilsHelper().keepUpTrend(condiData,0,i,self.dayWait)
            sell = UtilsHelper().keepDownTrend(condiData,-100,i,self.dayWait)

            maD = maL[i] - maL[i-self.cciLLen] if i-self.cciLLen >0 else maL[i] - maL[0]
            maD = maD/maL[i] > -0.03 if maL[i] is not None and maL[i] > 0 else True
            if buy and closeData[i] >= closeData[i-self.cciSLen] and maD:
                status = 1
            
            if sell and closeData[i] < closeData[i-self.cciSLen]:
                status = -1

            posData.append(status)
        return posData
