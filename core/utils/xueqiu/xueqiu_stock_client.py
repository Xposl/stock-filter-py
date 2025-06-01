"""
雪球股票数据客户端
专门处理雪球平台的股票查询、公司信息和历史数据
"""

import json
import pandas as pd
from typing import Optional

from .xueqiu_base_client import XueqiuBaseClient
from .xueqiu_company import XueqiuHkCompany, XueqiuUsCompany, XueqiuZhCompany
from .xueqiu_company import xueqiu_hk_company_from_dict, xueqiu_us_company_from_dict, xueqiu_zh_company_from_dict
from .xueqiu_stock_quote import XueqiuStockQuote, xueqiu_stock_quote_from_dict

import logging

logger = logging.getLogger(__name__)


class XueqiuStockClient(XueqiuBaseClient):
    """雪球股票数据客户端"""
    
    def get_client_type(self) -> str:
        """返回客户端类型"""
        return "stock"
    
    def get_stock_quote(self, code: str) -> Optional[XueqiuStockQuote]:
        """获取股票状态"""
        try:
            symbol = self._get_symbol(code)
            url = f'https://stock.xueqiu.com/v5/stock/quote.json?symbol={symbol}&extend=detail'
            
            content = self._sync_request(url)
            if content is None:
                return None
                
            json_data = json.loads(content)
            if ('data' not in json_data or 
                json_data['data'] is None or 
                'quote' not in json_data['data'] or 
                json_data['data']['quote'] is None):
                return None
                
            return xueqiu_stock_quote_from_dict(json_data['data'])
            
        except Exception as e:
            logger.error(f"获取股票报价失败 {code}: {e}")
            return None
    
    def get_zh_stock_company(self, code: str) -> Optional[XueqiuZhCompany]:
        """获取A股公司详情"""
        try:
            symbol = self._get_symbol(code)
            url = f'https://stock.xueqiu.com/v5/stock/f10/cn/company.json?symbol={symbol}'
            
            content = self._sync_request(url)
            if content is None:
                return None
                
            json_data = json.loads(content)
            # 增加数据检查，避免'company'键不存在的情况
            if ('data' not in json_data or 
                json_data['data'] is None or 
                'company' not in json_data['data'] or 
                json_data['data']['company'] is None):
                return None
                
            return xueqiu_zh_company_from_dict(json_data['data']['company'])
            
        except Exception as e:
            logger.error(f"获取A股公司详情失败 {code}: {e}")
            return None
    
    def get_hk_stock_company(self, code: str) -> Optional[XueqiuHkCompany]:
        """获取港股公司详情"""
        try:
            symbol = self._get_symbol(code)
            url = f'https://stock.xueqiu.com/v5/stock/f10/hk/company.json?symbol={symbol}'
        
            content = self._sync_request(url)
            if content is None:
                return None
                
            json_data = json.loads(content)
            if ('data' not in json_data or 
                json_data['data'] is None or 
                'company' not in json_data['data'] or 
                json_data['data']['company'] is None):
                return None
                
            return xueqiu_hk_company_from_dict(json_data['data']['company'])
            
        except Exception as e:
            logger.error(f"获取港股公司详情失败 {code}: {e}")
            return None
    
    def get_us_stock_company(self, code: str) -> Optional[XueqiuUsCompany]:
        """获取美股公司详情"""
        try:
            symbol = self._get_symbol(code)
            url = f'https://stock.xueqiu.com/v5/stock/f10/us/company.json?symbol={symbol}'
        
            content = self._sync_request(url)
            if content is None:
                return None
                
            json_data = json.loads(content)
            if ('data' not in json_data or 
                json_data['data'] is None or 
                'company' not in json_data['data'] or 
                json_data['data']['company'] is None):
                return None
                
            return xueqiu_us_company_from_dict(json_data['data']['company'])
            
        except Exception as e:
            logger.error(f"获取美股公司详情失败 {code}: {e}")
            return None
    
    def get_stock_history(self, code: str, start_date: str) -> Optional[pd.DataFrame]:
        """
        获取股票历史数据
        
        Args:
            code: 股票代码
            start_date: 开始日期 (格式: YYYY-MM-DD)
            
        Returns:
            包含历史数据的DataFrame或None
        """
        try:
            symbol = self._get_symbol(code)
            # 构建历史数据API URL
            url = f'https://stock.xueqiu.com/v5/stock/chart/kline.json?symbol={symbol}&begin={start_date}&period=day&type=before&count=-1'
            
            content = self._sync_request(url)
            if content is None:
                return None
                
            json_data = json.loads(content)
            if ('data' not in json_data or 
                json_data['data'] is None or 
                'item' not in json_data['data']):
                return None
            
            # 解析K线数据
            items = json_data['data']['item']
            if not items:
                return None
            
            # 转换为DataFrame
            df_data = []
            for item in items:
                if len(item) >= 6:  # 确保有足够的数据
                    df_data.append({
                        'timestamp': item[0],
                        'volume': item[1],
                        'open': item[2],
                        'high': item[3], 
                        'low': item[4],
                        'close': item[5],
                        'change_rate': item[6] if len(item) > 6 else None,
                        'turnover_rate': item[7] if len(item) > 7 else None
                    })
            
            if not df_data:
                return None
                
            df = pd.DataFrame(df_data)
            
            # 转换时间戳
            df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.set_index('date')
            
            # 按日期排序
            df = df.sort_index()
            
            logger.info(f"成功获取 {code} 历史数据，共 {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"获取股票历史数据失败 {code}: {e}")
            return None
    
    async def get_stock_quote_async(self, code: str) -> Optional[XueqiuStockQuote]:
        """异步获取股票状态"""
        try:
            symbol = self._get_symbol(code)
            url = f'https://stock.xueqiu.com/v5/stock/quote.json?symbol={symbol}&extend=detail'
            
            response_data = await self._async_request(url)
            if response_data is None:
                return None
                
            if ('data' not in response_data or 
                response_data['data'] is None or 
                'quote' not in response_data['data'] or 
                response_data['data']['quote'] is None):
                return None
                
            return xueqiu_stock_quote_from_dict(response_data['data'])
            
        except Exception as e:
            logger.error(f"异步获取股票报价失败 {code}: {e}")
            return None
    
    async def get_zh_stock_company_async(self, code: str) -> Optional[XueqiuZhCompany]:
        """异步获取A股公司详情"""
        try:
            symbol = self._get_symbol(code)
            url = f'https://stock.xueqiu.com/v5/stock/f10/cn/company.json?symbol={symbol}'
            
            response_data = await self._async_request(url)
            if response_data is None:
                return None
                
            if ('data' not in response_data or 
                response_data['data'] is None or 
                'company' not in response_data['data'] or 
                response_data['data']['company'] is None):
                return None
                
            return xueqiu_zh_company_from_dict(response_data['data']['company'])
            
        except Exception as e:
            logger.error(f"异步获取A股公司详情失败 {code}: {e}")
            return None
    
    async def get_hk_stock_company_async(self, code: str) -> Optional[XueqiuHkCompany]:
        """异步获取港股公司详情"""
        try:
            symbol = self._get_symbol(code)
            url = f'https://stock.xueqiu.com/v5/stock/f10/hk/company.json?symbol={symbol}'
            
            response_data = await self._async_request(url)
            if response_data is None:
                return None
                
            if ('data' not in response_data or 
                response_data['data'] is None or 
                'company' not in response_data['data'] or 
                response_data['data']['company'] is None):
                return None
                
            return xueqiu_hk_company_from_dict(response_data['data']['company'])
            
        except Exception as e:
            logger.error(f"异步获取港股公司详情失败 {code}: {e}")
            return None
    
    async def get_us_stock_company_async(self, code: str) -> Optional[XueqiuUsCompany]:
        """异步获取美股公司详情"""
        try:
            symbol = self._get_symbol(code)
            url = f'https://stock.xueqiu.com/v5/stock/f10/us/company.json?symbol={symbol}'
            
            response_data = await self._async_request(url)
            if response_data is None:
                return None
                
            if ('data' not in response_data or 
                response_data['data'] is None or 
                'company' not in response_data['data'] or 
                response_data['data']['company'] is None):
                return None
                
            return xueqiu_us_company_from_dict(response_data['data']['company'])
            
        except Exception as e:
            logger.error(f"异步获取美股公司详情失败 {code}: {e}")
            return None 