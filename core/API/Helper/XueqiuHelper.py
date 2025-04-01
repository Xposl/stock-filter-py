from http.cookiejar import CookieJar
import urllib.request
import gzip
import json
import datetime
import pandas as pd

from core.Enum.TickerType import TickerType

class Xueqiu:

    type = {
        0: TickerType.STOCK,
        4: TickerType.ETF,
        5: TickerType.STOCK,
        6: TickerType.STOCK,
        11: TickerType.STOCK,
        30: TickerType.STOCK,
        32: TickerType.WARRANT,
        33: TickerType.ETF,
        34: TickerType.BOND,
        82: TickerType.STOCK,
    }

    status = {
        0: 0, #未上市
        1: 1, #正常
        2: 0, #停牌
        3: 0, #退市
    }

    def __init__(self):
        cookie = CookieJar()
        handler = urllib.request.HTTPCookieProcessor(cookie)
        opener = urllib.request.build_opener(handler)
        opener.addheaders=[
            ('Host','xueqiu.com'),
            ('User-Agent','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'),
        ]
        opener.open('https://xueqiu.com/')
        for item in cookie:
            if item.name == 'xqat':
                self.xqat = item.value

    def _request(self,url):
        headers = {
            'Host': 'stock.xueqiu.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Accept-Encoding': 'gzip, deflatef',
            'Cookie': 'xqat={};'.format(self.xqat)
        }
        r = urllib.request.Request(url,headers=headers)
        return gzip.decompress(urllib.request.urlopen(r).read()).decode('utf-8')

    def getSymbol(self,code):
        if code.startswith('SZ') or code.startswith('SH'):
            return '%s%s'%(code[:2],code[3:])
        return code[3:]
    
    def checkSymbolStartswith(self,code,filters):
        symbol = self.getSymbol(code)
        for filter in filters:
            if symbol.startswith(filter):
                return True
        return False

    def checkNameWithStr(self,name,filters):
        for filter in filters:
            if name.find(filter) > -1:
                return True
        return False

    def getStockStatus(self,code):
        symbol = self.getSymbol(code)
        url = 'https://stock.xueqiu.com/v5/stock/quote.json?symbol=%s&extend=detail'%symbol
        
        content = self._request(url)
        if content is None:
            return None
        jsonData = json.loads(content)
        return jsonData['data']['quote']

    def getZHStockDetail(self,code,name):
        symbol = self.getSymbol(code)
        url = 'https://stock.xueqiu.com/v5/stock/f10/cn/company.json?symbol=%s'%symbol
        
        content = self._request(url)
        if content is None:
            return None
        jsonData = json.loads(content)
        listedDate = None

        result = {
            'code': code,
            'name': name
        }
        
        if jsonData['data']['company'] is None:
            return result

        if jsonData['data']['company']['org_cn_introduction'] is not None:
            result['remark'] = jsonData['data']['company']['org_cn_introduction']

        if jsonData['data']['company']['listed_date'] is not None:
            listedDate = jsonData['data']['company']['listed_date']
        elif jsonData['data']['company']['established_date'] is not None: 
            listedDate = jsonData['data']['company']['established_date']

        if listedDate is not None:
            if listedDate < 0:
                listedDate = '1970-01-01'
            else:
                result['listed_date'] = datetime.datetime.fromtimestamp(listedDate/1000).strftime('%Y-%m-%d')

        return result

    def getHKStockDetail(self,code,name):
        symbol = self.getSymbol(code)
        url = 'https://stock.xueqiu.com/v5/stock/f10/hk/company.json?symbol=%s'%symbol
    
        content = self._request(url)
        if content is None:
            return None
        jsonData = json.loads(content)

        result = {
            'code': code,
            'name': name
        }

        if jsonData['data']['company'] is None:
            return result
        
        if jsonData['data']['company']['comintr'] is not None:
            result['remark'] = jsonData['data']['company']['comintr']

        return result

    def getUSStockDetail(self,code,name):
        symbol = self.getSymbol(code)
        url = 'https://stock.xueqiu.com/v5/stock/f10/us/company.json?symbol=%s'%symbol
        
        content = self._request(url)
        if content is None:
            return None
        jsonData = json.loads(content)

        result = {
            'code': code,
            'name': name
        }

        if jsonData['data']['company'] is None:
            return result
        
        if jsonData['data']['company']['org_cn_introduction'] is not None:
            result['remark'] = jsonData['data']['company']['org_cn_introduction']

        listedDate = None
        if jsonData['data']['company']['listed_date'] is not None:
            listedDate = jsonData['data']['company']['listed_date']
        elif jsonData['data']['company']['established_date'] is not None: 
            listedDate = jsonData['data']['company']['established_date']

        if listedDate is not None:
            if listedDate < 0:
                listedDate = '1970-01-01'
            else:
                result['listed_date'] = datetime.datetime.fromtimestamp(listedDate/1000).strftime('%Y-%m-%d')
          
        return result

    def getStockDetail(self,code,name):
        data = None
        if code.startswith('US'):
            data = self.getUSStockDetail(code,name)
        elif code.startswith('HK'):
            data = self.getHKStockDetail(code,name)
        elif code.startswith('SZ') or code.startswith('SH'):
            data = self.getZHStockDetail(code,name)

        if data is not None:
            quote = self.getStockStatus(code)
            if quote is None:
                data['type'] = TickerType.DEL
                data['is_deleted'] = 1
                data['status'] = 0
                return data

            if quote['status'] in self.status:
                if quote['status'] == 0:
                    data['is_deleted'] = 1
                elif quote['status'] == 3:
                    data['delist'] = 1
                    data['is_deleted'] = 1
                data['status'] = self.status[quote['status']] if quote['open'] is not None else 0
            else:
                raise Exception('Unknown status',quote['status'])

            if quote['type'] in self.type:
                if quote['type'] == 32:
                    data['status'] = 0
                data['type'] = self.type[quote['type']]
            else:
                raise Exception('Unknown Type',quote['type'])
            
            data['lot_size'] = quote['lot_size'] if 'lot_size' in quote and quote['lot_size'] is not None else -1
            data['pe_forecast'] = quote['pe_forecast'] if 'pe_forecast' in quote and quote['pe_forecast'] is not None else -1
            data['pettm'] = quote['pe_ttm'] if 'pe_ttm' in quote and quote['pe_ttm'] is not None else -1
            data['pb'] = quote['pb'] if 'pb' in quote and quote['pb'] is not None else -1
            data['total_share'] = quote['total_shares'] if quote['total_shares'] is not None else -1
        return data

    def getStockHistory(self,code,startDate):
        startDate = datetime.datetime.strptime(startDate, "%Y-%m-%d")
        today = datetime.datetime.now()
        diff = int((today - startDate).days * 5/7)
        begin = int(today.timestamp()*1000)
        url = "http://stock.xueqiu.com/v5/stock/chart/kline.json?symbol=%s&begin=%s&period=day&type=before&count=-%s"%(code,begin,str(diff))

        content = self._request(url)
        if content is None:
            return None
        jsonData = json.loads(content)
        if jsonData is None or 'item' not in jsonData['data']:
            return None
        temp_df = pd.DataFrame(jsonData["data"]["item"])
        temp_df.columns = ["日期","成交量","开盘","最高","最低","收盘","chg","涨跌幅","换手率","成交额","volume_post","amount_post"]
        temp_df.reset_index(inplace=True)
        temp_df['index'] = range(1, len(temp_df)+1)
        temp_df.rename(columns={'index': "序号"}, inplace=True)
        temp_df = temp_df[[
            "日期",
            "最高",
            "最低",
            "开盘",
            "收盘",
            "涨跌幅",
            "换手率",
            "成交量",
            "成交额"
        ]]
        return temp_df

    