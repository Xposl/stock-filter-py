import pandas as pd

from core.enum.ticker_type import TickerType
from core.libs.utils import UtilsHelper
from core.service.ticker_score_repository import TickerScoreRepository

class TickerScoreFilter:

    def calculate(self,ticker,kLineData,strategyData,indicatorData,KScoreData,valuationData):
        if ticker['type'] != TickerType.STOCK.value:
            return False
        if ticker['code'].startswith('SH.688'):
            return False

        if ticker['pb'] > 25:
            return False
        
        if ticker['pettm'] >= 25 or ticker['pettm'] <= 0:
            return False

        
            
        weekKLineData = UtilsHelper().getWeekLine(kLineData)
        kLine = pd.DataFrame(kLineData)
        weekKLine = pd.DataFrame(weekKLineData)

        length = len(kLineData)
        weekLength = len(weekKLine)
        
        if length == 0:
            return False

        len5 = 5 if length > 5 else length
        len10 = 10 if length > 10 else length
        len20 = 20 if length > 20 else length
        

        # 7天交易额均线, 成交量放大
        maTurnover = UtilsHelper().SMA(kLine['turnover'].values,len5)
        if maTurnover[length-1] < 5 * 1000 * 1000:
            return False

        KScoreData = TickerScoreRepository().get_items_by_ticker_id(ticker['id'])
        kScore = pd.DataFrame(KScoreData)
        maS = UtilsHelper().WMA(kScore['score'].values,len5)
        maM = UtilsHelper().WMA(kScore['score'].values,len10)
        maL = UtilsHelper().WMA(kScore['score'].values,len20)

        weekMa5 = UtilsHelper().EMA(weekKLine['close'].values,len5)
        ma20 = UtilsHelper().EMA(kLine['close'].values,len20)
        
        lastIndex = length - 1
        lastWeekIndex = weekLength - 1
        close = kLine['close'][lastIndex]

        if close * ticker['total_share'] > 50 * 1000 * 1000 * 1000:
            return False

        if (maS[lastIndex] >= maM[lastIndex] and maM[lastIndex] > maL[lastIndex] and kScore['score'][lastIndex] > 60) or maS[lastIndex] > 60:
            if close > weekMa5[lastWeekIndex] and  close > ma20[lastIndex]:
                return True
        return False
