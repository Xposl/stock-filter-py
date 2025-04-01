import akshare as ak
import datetime

from core.API import APIHelper
from core.API.Helper.XueqiuHelper import Xueqiu
from core.utils import UtilsHelper

class DongcaiTicker:
    def getCHTickers(self):
        result = []
        tickers = ak.stock_zh_a_spot_em()
        for i in range(len(tickers)):
            code = tickers['代码'][i]
            if code.startswith('0') or code.startswith('3'):
                code  = 'SZ.%s'%str(code)
            elif code.startswith('6') or code.startswith('7') or code.startswith('9'):
                code  = 'SH.%s'%str(code)
            elif code.startswith('83') or code.startswith('87') or code.startswith('88'):
                code  = 'BJ.%s'%str(code)
                ## TODO: 跳过北交所
                continue
            else:
                continue

            result.append({
                'code': code,
                'name': tickers['名称'][i],
                'source': 1
            })
        return result

    def getHKTickers(self):
        result = []
        tickers = ak.stock_hk_spot_em()
        for i in range(len(tickers)):
            result.append({
                'code': 'HK.%s'%tickers['代码'][i],
                'name': tickers['名称'][i],
                'source': 1
            })
        return result

    def getUSTickers(self):
        result = []
        tickers = ak.stock_us_spot_em()
        for i in range(len(tickers)):
            result.append({
                'code': 'US.%s'%tickers['代码'][i][4:],
                'name': tickers['名称'][i],
                'source': 1
            })
        return result

    def updateTickers(self):
        result = []
        result += self.getHKTickers()
        result += self.getUSTickers()
        result += self.getCHTickers()
        return result


class Ticker:
    source = []

    updateTime = ''
    APIHelper = APIHelper()

    def __init__(self,updateTime):
        self.source.append(DongcaiTicker())
        self.updateTime = updateTime

    def updateTickerList(self):
        data = {}
        for source in self.source:
            tickers = source.updateTickers()
            for ticker in tickers:
                code = ticker['code']
                if code not in data:
                    data[code] = ticker
        return data

    def updateTickerDetail(self,code,name):
        ticker = Xueqiu().getStockDetail(code,name)
        if ticker is not None:
            ticker['type'] = ticker['type'].value
        return ticker
    
    def getTickerDetail(self, ticker):
        newTicker = self.updateTickerDetail(ticker['code'],ticker['name'])
        newTicker['modify_time'] = datetime.datetime.now().strftime('%Y-%m-%d')
        if 'source' not in ticker or ticker['source'] is None:
                newTicker['source'] = 1
        else:
            newTicker['source'] = ticker['source']
        return newTicker
    
    def updateTickers(self):
        tickerList = self.updateTickerList()
        tickers = self.APIHelper.ticker().getAllMapItems()
        i = 0
        total = len(tickerList)
        for code in tickerList:
            UtilsHelper().runProcess(i,total,"添加新股","{}".format(code))
            if code not in tickers:
                ticker = tickerList[code]
                # 新股
                newTicker = self.getTickerDetail(ticker)
                self.APIHelper.ticker().insertItem(newTicker['code'],newTicker['name'],newTicker, i%100 == 0 or i == total - 1)
            i += 1

        i = 0
        total = len(tickers)
        for code in tickers:
            ticker = tickers[code]
            UtilsHelper().runProcess(i,total,"更新现有股","{}".format(code))
            if (code not in tickerList and ticker['modify_time'].strftime('%Y-%m-%d') < datetime.datetime.now().strftime('%Y-%m-%d')) or (code in tickerList and tickers[code]['name'] != tickerList[code]['name']):
                print('更新项目:'+code)
                # 变动股
                newTicker = self.getTickerDetail(ticker)
                self.APIHelper.ticker().updateItem(newTicker['code'],newTicker['name'],newTicker)
            i += 1
  
