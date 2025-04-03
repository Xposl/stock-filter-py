import os
import gzip
import json
import datetime
import pandas as pd
import asyncio
import urllib.request
from pyppeteer import launch

from core.enum.ticker_type import TickerType

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

    async def get_token_with_puppeteer(self):
        """使用pyppeteer获取雪球的token"""
        try:
            # 获取环境变量或使用默认设置
            chromium_executable_path = os.environ.get('PYPPETEER_CHROMIUM_PATH')
            
            # 构建launch参数
            launch_args = {
                'headless': True,  # 设置为无头模式
                'args': ['--no-sandbox', '--disable-setuid-sandbox']
            }
            
            # 如果环境变量中指定了chromium路径，则使用它
            if chromium_executable_path and os.path.exists(chromium_executable_path):
                launch_args['executablePath'] = chromium_executable_path
            
            browser = await launch(**launch_args)
            page = await browser.newPage()
            
            # 设置User-Agent
            await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36')
            
            # 访问雪球网站
            await page.goto('https://xueqiu.com/', {'waitUntil': 'networkidle0'})
            
            # 获取所有cookie
            cookies = await page.cookies()
            xqat = None
            
            # 查找xqat cookie
            for cookie in cookies:
                if cookie.get('name') == 'xqat':
                    xqat = cookie.get('value')
                    break
            
            await browser.close()
            return xqat
        except Exception as e:
            print(f"使用puppeteer获取token失败: {e}")
            return None

    def get_token_with_urllib(self):
        """使用urllib获取雪球token（备用方法）"""
        try:
            from http.cookiejar import CookieJar
            
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
                    return item.value
            
            return None
        except Exception as e:
            print(f"使用urllib获取token失败: {e}")
            return None

    def __init__(self):
        """初始化Xueqiu类，初始token为None，只在需要时获取"""
        # 初始化时不获取token，只在真正需要时才获取
        self.xqat = None

    def _get_token(self):
        """获取雪球token，如果还没有获取过或之前获取失败"""
        if self.xqat:
            return True
            
        # 首先尝试使用puppeteer获取token
        self.xqat = asyncio.get_event_loop().run_until_complete(self.get_token_with_puppeteer())
        
        # 如果puppeteer失败，尝试使用urllib作为备用方法
        if not self.xqat:
            print("使用puppeteer获取token失败，尝试使用备用方法...")
            self.xqat = self.get_token_with_urllib()
        
        # 如果两种方法都失败，返回False
        if not self.xqat:
            print("无法获取雪球token，请检查网络连接或尝试更新User-Agent")
            return False
        
        print("成功获取雪球token")
        return True

    def _request(self, url, retry=True):
        """发送HTTP请求并处理响应
        
        Args:
            url: 请求的URL
            retry: 是否在请求失败时尝试重新获取token并重试
            
        Returns:
            解码后的响应内容
        """
        # 确保有token
        if not self.xqat and not self._get_token():
            if retry:
                print("首次获取token失败，正在重试...")
                if not self._get_token():
                    raise Exception("无法获取雪球token，请检查网络连接或尝试更新User-Agent")
            else:
                return None
                
        headers = {
            'Host': 'stock.xueqiu.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Accept-Encoding': 'gzip, deflatef',
            'Cookie': 'xqat={};'.format(self.xqat)
        }
        
        try:
            r = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(r)
            return gzip.decompress(response.read()).decode('utf-8')
        except Exception as e:
            # 如果请求失败且允许重试，则尝试重新获取token并重试
            if retry:
                print(f"请求失败: {e}，正在尝试重新获取token...")
                # 重置token并重新获取
                self.xqat = None
                if not self._get_token():
                    raise Exception("无法获取雪球token，请检查网络连接或尝试更新User-Agent")
                # 重新请求（禁用重试以避免无限循环）
                return self._request(url, retry=False)
            else:
                # 重试失败，抛出异常
                print(f"重试失败: {e}")
                return None

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
        # 增加数据检查，避免'data'或'quote'键不存在的情况
        if 'data' not in jsonData or jsonData['data'] is None or 'quote' not in jsonData['data'] or jsonData['data']['quote'] is None:
            return None
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
        
        # 增加数据检查，避免'company'键不存在的情况
        if 'data' not in jsonData or jsonData['data'] is None or 'company' not in jsonData['data'] or jsonData['data']['company'] is None:
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

        # 增加数据检查，避免'company'键不存在的情况
        if 'data' not in jsonData or jsonData['data'] is None or 'company' not in jsonData['data'] or jsonData['data']['company'] is None:
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

        # 增加数据检查，避免'company'键不存在的情况
        if 'data' not in jsonData or jsonData['data'] is None or 'company' not in jsonData['data'] or jsonData['data']['company'] is None:
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
        # 增加数据检查，避免'data'键不存在的情况
        if jsonData is None or 'data' not in jsonData or jsonData['data'] is None or 'item' not in jsonData['data']:
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
