import pandas as pd

from core.enum.ticker_type import TickerType
from core.libs.utils import UtilsHelper
from core.service import APIHelper

class TickerSQJZFilter:

    def calculate(self,ticker,kLineData,strategyData,indicatorData,KScoreData,valuationData):
        if ticker['type'] != TickerType.STOCK.value:
            return False
        if ticker['code'].startswith('SH.688'):
            return False

        length = len(kLineData)
        kLine = pd.DataFrame(kLineData)
        if length < 9:
            return False

        len7 = 7 if length > 7 else length
        len13 = 13 if length > 13 else length
        len21 = 21 if length > 21 else length
        
        # 7天交易额均线
        maTurnover = UtilsHelper().SMA(kLine['turnover'].values,len13)
        nt = 0
        for i in range(length):
            if length - i - 2 < 0:
                break
            if kLine['close'][length - i - 1] < kLine['close'][length - i - 2]:
                nt += 1
            else:
                break
        if maTurnover[length-1] < 10 * 1000 * 1000 and nt < 4:
            return False

        KScoreData = APIHelper().tickerScore().getItemsByTickerId(ticker['id'])
        kScore = pd.DataFrame(KScoreData)
        maS = UtilsHelper().WMA(kScore['score'].values,len7)
        maM = UtilsHelper().WMA(kScore['score'].values,len13)
        maL = UtilsHelper().WMA(kScore['score'].values,len21)


        lastIndex = length - 1
        # 神奇九转
        ntu = 0
        ntd = 0
        for i in range(length):
            if lastIndex - i - 4 < 0:
                break
            if kLine['close'][lastIndex - i] < kLine['close'][lastIndex - i - 4]:
                ntd += 1
            else:
                break
        
        for i in range(length):
            if lastIndex - i - 4 < 0:
                break
            if kLine['close'][lastIndex - i] > kLine['close'][lastIndex - i - 4]:
                ntu += 1
            else:
                break

        if (maS[lastIndex] >= maM[lastIndex] and maM[lastIndex] > maL[lastIndex] and kScore['score'][lastIndex] > 50) or maS[lastIndex] > 60: # 趋势分数要足够高
            if ntu >= 2 and ntu < 5:
                return True
            if ntd == 9:
                return True

        return False
