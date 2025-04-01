import akshare as ak
import datetime
import math

from core.Enum.TickerType import TickerType
from core.API import APIHelper
from core.API.Helper.XueqiuHelper import Xueqiu


class dongcaiSource:
    def __init__(self,code,startDate,endDate):
        self.code = code
        self.startDate = startDate
        self.endDate = endDate

    def getDataTimeKey(self,data,index):
        return data['日期'][index]

    def convertData(self,data,index):
        return {
            'time_key': data['日期'][index],
            'high': data['最高'][index],
            'low': data['最低'][index],
            'open': data['开盘'][index],
            'close': data['收盘'][index],
            'volume': data['成交量'][index],
            'turnover': data['成交额'][index],
            'turnover_rate': data['换手率'][index]
        }

    def convertOnTimeData(self,data,index):
        return {
            'time_key': datetime.date.today(),
            'high': data['最高'][index],
            'low': data['最低'][index],
            'open': data['今开'][index],
            'close': data['最新价'][index],
            'volume': data['成交量'][index],
            'turnover': data['成交额'][index],
            'turnover_rate': 0
        }

    def convertUSOnTimeData(self,data,index):
        return {
            'time_key': datetime.date.today(),
            'high': data['最高价'][index],
            'low': data['最低价'][index],
            'open': data['开盘价'][index],
            'close': data['最新价'][index],
            'volume': 0,
            'turnover': 0,
            'turnover_rate': 0
        }

    def getZHOnTimeData(self):
        tickers = ak.stock_zh_a_spot_em()
        for i in range(len(tickers)):
            code = tickers['代码'][i]
            if code.startswith('0') or code.startswith('3'):
                code  = 'SZ.%s'%str(code)
            elif code.startswith('6') or code.startswith('7') or code.startswith('9'):
                code  = 'SH.%s'%str(code)
            if code == self.code:
                return self.convertOnTimeData(tickers,i)
        return None

    def getHKOnTimeData(self):
        tickers = ak.stock_hk_spot_em()
        for i in range(len(tickers)):
            code = 'HK.%s'%tickers['代码'][i]
            if code == self.code:
                return self.convertOnTimeData(tickers,i)
        return None

    def getUSOnTimeData(self):
        tickers = ak.stock_us_spot_em()
        for i in range(len(tickers)):
            code = 'US.%s'%tickers['代码'][i][4:]
            if code == self.code:
                return self.convertUSOnTimeData(tickers,i)
        return None

    def getOnTimeKLineData(self):
        data = None
        if self.code.startswith('US'):
            data = self.getUSOnTimeData()
        elif self.code.startswith('HK'):
            data = self.getHKOnTimeData()
        elif self.code.startswith('SZ') or self.code.startswith('SH'):
            data = self.getZHOnTimeData()
        
        if data is not None:
            data['id'] = 0
        return data

    def getKLineData(self):
        data = None
        startDate = datetime.datetime.strptime(self.startDate, "%Y-%m-%d").strftime('%Y%m%d')
        endDate = datetime.datetime.strptime(self.endDate, "%Y-%m-%d").strftime('%Y%m%d')
        if self.code.startswith('US'):
            data = ak.stock_us_hist(symbol='105.'+self.code[3:],start_date=startDate, end_date=endDate, adjust="qfq")
        elif self.code.startswith('HK'):
            data = ak.stock_hk_hist(symbol=self.code[3:],start_date=startDate, end_date=endDate, adjust="qfq")
        elif self.code.startswith('SZ') or self.code.startswith('SH'):
            data = ak.stock_zh_a_hist(symbol=self.code[3:],start_date=startDate, end_date=endDate, adjust="qfq")
        return data

class sinaSource: 
    def __init__(self,code,startDate,endDate):
        self.code = code
        self.startDate = startDate
        self.endDate = endDate
        self.type = 0

    def getDataTimeKey(self,data,index):
        if self.type == 1:
            return data.index[index].strftime('%Y-%m-%d')
        return  data['date'][index] if type(data['date'][index]) == str else data['date'][index].strftime('%Y-%m-%d')

    def convertData(self,data,index):
        return {
            'time_key': self.getDataTimeKey(data,index),
            'high': data['high'][index],
            'low': data['low'][index],
            'open': data['open'][index],
            'close': data['close'][index],
            'volume': data['volume'][index],
            'turnover': data['volume'][index] * data['low'][index],
            'turnover_rate': 0
        }

    def getKLineData(self):
        data = None
        if self.code.startswith('US'):
            data = ak.stock_us_daily(symbol=self.code[3:], adjust="qfq")
            self.type = 1
        elif self.code.startswith('HK'):
            data = ak.stock_hk_daily(symbol=self.code[3:], adjust="qfq")
        elif self.code.startswith('SZ'):
            data = ak.stock_zh_a_daily(symbol='sz'+self.code[3:], end_date=self.endDate, adjust="qfq")
        elif self.code.startswith('SH'):
            data = ak.stock_zh_a_daily(symbol='sh'+self.code[3:], end_date=self.endDate, adjust="qfq")
        return data

class xueqiuSource:
    def __init__(self,code,startDate,endDate):
        self.code = code
        self.startDate = startDate
        self.endDate = endDate

    def getDataTimeKey(self,data,index):
        return datetime.datetime.fromtimestamp(data['日期'][index]/1000).strftime('%Y-%m-%d')

    def convertData(self,data,index):
        return {
            'time_key': self.getDataTimeKey(data,index),
            'high': data['最高'][index],
            'low': data['最低'][index],
            'open': data['开盘'][index],
            'close': data['收盘'][index],
            'volume': data['成交量'][index],
            'turnover': 0 if math.isnan(data['成交额'][index]) else data['成交额'][index],
            'turnover_rate': 0 if math.isnan(data['换手率'][index]) else data['换手率'][index]
        }

    def getKLineData(self):
        if self.code.startswith('US') or self.code.startswith('HK'):
            data = Xueqiu().getStockHistory(self.code[3:],self.startDate)
        elif self.code.startswith('SZ'):
            data = Xueqiu().getStockHistory('SZ'+self.code[3:],self.startDate)
        elif self.code.startswith('SH'):
            data = Xueqiu().getStockHistory('SH'+self.code[3:],self.startDate)
        return data

class TickerKLine:
    tickerType = [
        TickerType.STOCK,
        TickerType.IDX,
        TickerType.ETF,
        TickerType.PLATE
    ]
    endDate = ''
    startDate = ''

    APIHelper = APIHelper()

    def __init__(self,code,source,startDate,endDate):
        self.code = code
        self.source = source
        self.startDate = startDate
        self.endDate = endDate
        if self.source == 1:
            self.dataSource = dongcaiSource(self.code,self.startDate,self.endDate)
        elif self.source == 2:
            self.dataSource = sinaSource(self.code,self.startDate,self.endDate)
        elif self.source == 3:
            self.dataSource = xueqiuSource(self.code,self.startDate,self.endDate)
        else:
            raise Exception("未知数据源",self.source)
    

    def getKLine(self):
        result = []
        data = self.dataSource.getKLineData()
        if data is None:
            print('数据失效source:%s'%self.source)
            return None
        for i in range(len(data)):
            timeKey = self.dataSource.getDataTimeKey(data,i)
            if timeKey >= self.startDate and timeKey <= self.endDate:
                result.append(self.dataSource.convertData(data,i))
        return result

    def getKLineOnTime(self):
        return dongcaiSource(self.code,self.startDate,self.endDate).getOnTimeKLineData()

    # 更新个股K线
    def updateTickerKLine(self,ticker,force=False):
        tickerId = ticker['id']
        startDate = ticker['listed_date'].strftime('%Y-%m-%d') if ticker['listed_date'] is not None and self.startDate < ticker['listed_date'].strftime('%Y-%m-%d') else self.startDate
        updateTime = ticker['update_date'].strftime('%Y-%m-%d') if ticker['update_date'] is not None else None
        
        if startDate < self.endDate:
            if TickerType(ticker['type']) not in self.tickerType:
                print('[%s](%s)%s不在期望交易类型中将被移除'%(str(ticker['id']),ticker['code'],ticker['name']))
                ticker['is_deleted'] = 1
                self.APIHelper.ticker().updateItem(ticker['code'],ticker['name'],ticker)
                return
            try:
                klineItems = self.getKLine()
                ticker['status'] = 1

                if klineItems is not None:
                    kLineLength = len(klineItems)
                    if kLineLength > 0:
                        lastData = klineItems[len(klineItems) - 1]
                        lastUpdate = lastData['time_key']
    
                        if updateTime is None or lastUpdate > updateTime or force:
                            self.APIHelper.tickerDayLine().clearItemsByTickerId(tickerId)
                            self.APIHelper.tickerDayLine().updateItems(tickerId,klineItems)
                            clone_fields = ['time_key','open','close','low','high','turnover','turnover_rate','volume']
                            ticker['status'] = 1
                            ticker['is_deleted'] = 0
                            for clone_field in clone_fields:
                                ticker[clone_field] = lastData[clone_field]
                            ticker['update_date'] = lastUpdate 
                    else:
                        print("无日线数据")
                        ticker['status'] = 0
                else:
                    print("找不到日线数据")
                    ticker['status'] = 0
            except Exception as e:
                ticker['source'] = ticker['source']%3 + 1
                print('失败:',e)
            self.APIHelper.ticker().updateItem(ticker['code'],ticker['name'],ticker)

            
 
    