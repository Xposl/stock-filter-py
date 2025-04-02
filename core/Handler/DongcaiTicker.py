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