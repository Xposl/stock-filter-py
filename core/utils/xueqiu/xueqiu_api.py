import os
import gzip
import json
import datetime
from typing import Optional
import pandas as pd
import asyncio
import urllib.request
import ssl
from pyppeteer import launch

from core.utils.xueqiu.xueqiu_company import XueqiuHkCompany, XueqiuUsCompany, XueqiuZhCompany, xueqiu_hk_company_from_dict, xueqiu_us_company_from_dict, xueqiu_zh_company_from_dict
from core.utils.xueqiu.xueqiu_stock_quote import XueqiuStockQuote, xueqiu_stock_quote_from_dict


class XueqiuApi:

    def __init__(self):
        """初始化Xueqiu类，初始token为None，只在需要时获取"""
        # 初始化时不获取token，只在真正需要时才获取
        self.xqat = None

    async def _get_token_with_puppeteer(self) -> Optional[str]:
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

    def _get_token_with_urllib(self):
        """使用urllib获取雪球token（备用方法）"""
        try:
            from http.cookiejar import CookieJar
            
            # 创建一个不验证证书的SSL上下文
            context = ssl._create_unverified_context()
            
            cookie = CookieJar()
            handler = urllib.request.HTTPCookieProcessor(cookie)
            opener = urllib.request.build_opener(handler)
            opener.addheaders=[
                ('Host','xueqiu.com'),
                ('User-Agent','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'),
            ]
            
            # 使用SSL上下文打开URL
            opener.open('https://xueqiu.com/', context=context)
            
            for item in cookie:
                if item.name == 'xqat':
                    return item.value
            
            return None
        except Exception as e:
            print(f"使用urllib获取token失败: {e}")
            return None

    def _get_token(self):
        """获取雪球token，如果还没有获取过或之前获取失败"""
        if self.xqat:
            return True
            
        # 首先尝试使用puppeteer获取token
        self.xqat = asyncio.get_event_loop().run_until_complete(self._get_token_with_puppeteer())
        
        # 如果puppeteer失败，尝试使用urllib作为备用方法
        if not self.xqat:
            print("使用puppeteer获取token失败，尝试使用备用方法...")
            self.xqat = self._get_token_with_urllib()
        
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
            # 创建一个不验证证书的SSL上下文（注意：在生产环境中不推荐这么做）
            context = ssl._create_unverified_context()
            r = urllib.request.Request(url, headers=headers)
            response = urllib.request.urlopen(r, context=context)
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

    def _get_symbol(self,code):
        """转化股票代码"""
        if code.startswith('SZ') or code.startswith('SH'):
            return '%s%s'%(code[:2],code[3:])
        return code[3:]

    def get_stock_quote(self,code: str) -> Optional[XueqiuStockQuote]:
        """获取股票状态"""
        symbol = self._get_symbol(code)
        url = 'https://stock.xueqiu.com/v5/stock/quote.json?symbol=%s&extend=detail'%symbol
        
        content = self._request(url)
        if content is None:
            return None
        json_data = json.loads(content)
        if 'data' not in json_data or json_data['data'] is None or 'quote' not in json_data['data'] or json_data['data']['quote'] is None:
            return None
        return xueqiu_stock_quote_from_dict(json_data['data'])
    
    def get_zh_stock_company(self, code: str) -> Optional[XueqiuZhCompany]:
        """获取A股公司详情"""
        symbol = self._get_symbol(code)
        url = 'https://stock.xueqiu.com/v5/stock/f10/cn/company.json?symbol=%s'%symbol
        
        content = self._request(url)
        if content is None:
            return None
        json_data = json.loads(content)
        # 增加数据检查，避免'company'键不存在的情况
        if 'data' not in json_data or json_data['data'] is None or 'company' not in json_data['data'] or json_data['data']['company'] is None:
            return None
        return xueqiu_zh_company_from_dict(json_data['data']['company'])
    
    def get_hk_stock_company(self,code :str) -> Optional[XueqiuHkCompany]:
        """获取港股公司详情"""
        symbol = self._get_symbol(code)
        url = 'https://stock.xueqiu.com/v5/stock/f10/hk/company.json?symbol=%s'%symbol
    
        content = self._request(url)
        if content is None:
            return None
        json_data = json.loads(content)
        # 增加数据检查，避免'company'键不存在的情况
        if 'data' not in json_data or json_data['data'] is None or 'company' not in json_data['data'] or json_data['data']['company'] is None:
            return None
        return xueqiu_hk_company_from_dict(json_data['data']['company'])
    
    def get_us_stock_company(self,code :str) -> Optional[XueqiuUsCompany]:
        """获取美股公司详情"""
        symbol = self._get_symbol(code)
        url = 'https://stock.xueqiu.com/v5/stock/f10/us/company.json?symbol=%s'%symbol
        
        content = self._request(url)
        if content is None:
            return None
        json_data = json.loads(content)
        # 增加数据检查，避免'company'键不存在的情况
        if 'data' not in json_data or json_data['data'] is None or 'company' not in json_data['data'] or json_data['data']['company'] is None:
            return None
        return xueqiu_us_company_from_dict(json_data['data']['company'])
    
    def get_stock_history(self,code: str,startDate: str) -> Optional[pd.DataFrame]:
        """获取股票历史数据"""
        startDate = datetime.datetime.strptime(startDate, "%Y-%m-%d")
        today = datetime.datetime.now()
        diff = int((today - startDate).days * 5/7)
        begin = int(today.timestamp()*1000)
        url = "http://stock.xueqiu.com/v5/stock/chart/kline.json?symbol=%s&begin=%s&period=day&type=before&count=-%s"%(code,begin,str(diff))

        content = self._request(url)
        if content is None:
            return None
        json_data = json.loads(content)
        # 增加数据检查，避免'data'键不存在的情况
        if json_data is None or 'data' not in json_data or json_data['data'] is None or 'item' not in json_data['data']:
            return None
        temp_df = pd.DataFrame(json_data["data"]["item"])
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


