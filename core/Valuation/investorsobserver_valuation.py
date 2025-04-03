import gzip

import requests
import urllib.request
from http.cookiejar import CookieJar
from dateutil.parser import parse
import datetime
import json

class InvestorsobserverValuation:
                
    def getKey(self):
        return 'Research_Report_Valuation'
 
    def _request(self,url):
        apiToken = '5e9d3cf6ae7b6770f3003fe47223433cca3cbf0d'
        headers = {
            'Host': 'hercules-api.investorsobserver.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cookie': 'apiToken={};'.format(apiToken)
        }
        r = urllib.request.Request(url,headers=headers)
        f = urllib.request.urlopen(r, timeout=30)
        content =  gzip.decompress(f.read()).decode('utf-8')
        f.close()
        return content
    
    def getUSValuation(self,code):
        url = "https://hercules-api.investorsobserver.com/api/stock/"+code
        try:
            content = self._request(url)
            
            if content is None:
                return None
            data = json.loads(content)
            
            if 'data' in data and data['data']['priceMeanTarget'] is not None:
                return {
                    'time_key': datetime.date.today().strftime('%Y-%m-%d %H:%M:%S'), #更新时间
                    'target_price':data['data']['priceMeanTarget'], #平均目标价
                    'max_target_price':data['data']['priceHighTarget'], #最高目标价
                    'min_target_price':data['data']['priceLowTarget'], #最低目标价,
                    'remark': url
                }
        except urllib.error.URLError as e:
            print('error，估值连接错误',url,e.reason)
        return {
            'time_key': datetime.date.today().strftime('%Y-%m-%d %H:%M:%S'), #更新时间
            'target_price':-1, #平均目标价
            'max_target_price':-1, #最高目标价
            'min_target_price':-1, #最低目标价,
            'remark': url
        }

    def getHKValuation(self,code):
        url = "http://emweb.securities.eastmoney.com/PC_HKF10/InvestmentRating/PageAjax?code="+code
        res = requests.get( url )
        data = json.loads( res.text)
        if data is None or ('tzpj' in data) == False:
            return None
        items = data['tzpj']
        values = []
        size = 0
        today = datetime.date.today().strftime('%Y-%m-%d %H:%M:%S')

        if len(items) > 0 :
            for item in items:
                reportDate = parse(item['fbrq'])
                if (parse(today) - reportDate).days > 180:
                    continue
                if item['mbjg'] != '--':
                    targetValues = item['mbjg'].split('-')
                    for targetValue in targetValues:
                        size += 1
                        values.append(float(targetValue))
            if size > 0:
                return {
                    'time_key': today, #更新时间
                    'target_price': round(sum(values)/size,2) if size > 0 else -1, #平均目标价
                    'max_target_price': max(values) if len(values) > 0 else -1, #最高目标价
                    'min_target_price': min(values) if len(values) > 0 else -1, #最低目标价,
                    'remark': url
                }
        return {
            'time_key': today, #更新时间
            'target_price':  -1, #平均目标价
            'max_target_price': -1, #最高目标价
            'min_target_price': -1, #最低目标价,
            'remark': url
        }

    
    def calculate(self,ticker):
        code = ticker.code
        if code.startswith('US'):
            return self.getUSValuation(code[3:])
        if code.startswith('HK'):
            return self.getHKValuation(code[3:])
            
        return None
