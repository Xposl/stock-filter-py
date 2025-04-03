import pandas as pd

from core.enum.ticker_type import TickerType
from core.utils import UtilsHelper
from core.service import APIHelper

class TickerHighValuation:
    
    capacity = 50
    strategyId = None

    def __init__(self):
        rTickers = self.getValuationItems()
        tickerData = pd.DataFrame(rTickers)
        if 'code' in tickerData:
            self.tickerList = tickerData['code'].values
        else:
            self.tickerList = []
        strategy = APIHelper().strategy().getItemByKey('CCI_WMA_strategy')
        self.strategyId = strategy['id']

    def getValuationItems(self):
        connection = APIHelper().getMysqlEnv()
        with connection.cursor() as cursor:
            sql = "SELECT tt.* FROM (SELECT t.id, t.name, t.code, t.close, tv.max_target_price, tv.min_target_price, tv.target_price AS target_price, (tv.target_price - t.close)/t.close * 100 AS op FROM `ticker` AS t LEFT JOIN `ticker_valuation` AS tv ON tv.ticker_id = t.id AND tv.valuation_id = 1 WHERE target_price != -1) AS tt "
            sql += "WHERE tt.op < %s ORDER BY op desc"
            cursor.execute(sql% (self.capacity))
            return cursor.fetchall()

    def calculate(self,ticker,kLineData,strategyData,indicatorData,KScoreData,valuationData):
        if ticker['type'] != TickerType.STOCK.value:
            return False
        if ticker['code'].startswith('SH.688'):
            return False
        if ticker['code'] in self.tickerList:
            return False

        kLine = pd.DataFrame(kLineData)

        length = len(kLineData)
        
        if length == 0:
            return False

        len5 = 5 if length > 5 else length
        len10 = 10 if length > 10 else length
        len20 = 20 if length > 20 else length
        
        # 7天交易额均线, 成交量放大
        maTurnover = UtilsHelper().SMA(kLine['turnover'].values,len5)
        if maTurnover[length-1] < 5 * 1000 * 1000:
            return False

        KScoreData = APIHelper().tickerScore().getItemsByTickerId(ticker['id'])
        kScore = pd.DataFrame(KScoreData)
        maS = UtilsHelper().WMA(kScore['score'].values,len5)
        maM = UtilsHelper().WMA(kScore['score'].values,len10)
        maL = UtilsHelper().WMA(kScore['score'].values,len20)

        ma5 = UtilsHelper().EMA(kLine['close'].values,len5)
        
        lastIndex = length - 1
        close = kLine['close'][lastIndex]

        if close * ticker['total_share'] > 50 * 1000 * 1000 * 1000:
            return False

        strategy = None
        for s in strategyData:
            if self.strategyId == s['strategy_id']:
                strategy = s
        if (
            maS[lastIndex] >= maM[lastIndex] and
            maM[lastIndex] > maL[lastIndex] and 
            kScore['score'][lastIndex] > maL[lastIndex] and 
            kScore['score'][lastIndex] > 60 and maM[lastIndex] < 60
           ) :
            if strategy['status'] == 1:
                return True
        return False
