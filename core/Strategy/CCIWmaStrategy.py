from core.utils import UtilsHelper

class CCIWmaStrategy:
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
        return 'CCI_WMA_strategy'
    
    def calculate(self,klData):
        length = len(klData)
        closeData = []
        stopData = [0,0]
        posData = []

        for klItem in klData:
            closeData.append(klItem['close'])
        cciS = UtilsHelper().CCI(klData,self.cciSLen)
        cciM = UtilsHelper().CCI(klData,self.cciMLen)
        cciL = UtilsHelper().CCI(klData,self.cciLLen)

        maS = UtilsHelper().WMA(closeData,self.cciSLen)
        maM = UtilsHelper().WMA(closeData,self.cciMLen)
        maL = UtilsHelper().WMA(closeData,self.cciLLen)

        for i in range(2,len(klData)):
            isShort = -1 if maM[i-2] > maL[i-2] and maM[i-1] <= maL[i-1] else stopData[i-1]
            isLong = 1 if maS[i-2] < maM[i-2] and maS[i-1] >= maM[i-1] else isShort
            stopData.append(isLong)
        
        
        status = 0
        for i in range(length):
            cciUS = UtilsHelper().keepUpTrend(cciS,100,i,self.dayWait)
            cciUM = UtilsHelper().keepUpTrend(cciM,-100,i,self.dayWait)
            cciUL = UtilsHelper().keepUpTrend(cciL,-100,i,self.dayWait)
            cciDS = UtilsHelper().keepDownTrend(cciS,-100,i,self.dayWait)
            cciDM = UtilsHelper().keepDownTrend(cciM,100,i,self.dayWait)
            cciDL = UtilsHelper().keepDownTrend(cciL,100,i,self.dayWait)

            ## 逻辑测试
            cciLong = cciUS and cciUM and cciUL
            cciShort = cciDS and cciDM and cciDL

            buy = cciLong and stopData[i] == 1
            sell = cciShort and stopData[i] == -1

            if buy:
                status = 1
            
            if sell:
                status = -1
            posData.append(status)
        return posData
