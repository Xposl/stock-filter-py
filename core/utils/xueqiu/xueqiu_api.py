"""
雪球API - 重构版本
现在使用统一的雪球客户端抽象层
"""

import logging
from typing import Optional

import pandas as pd

from .xueqiu_client_factory import create_stock_client
from .xueqiu_company import XueqiuHkCompany, XueqiuUsCompany, XueqiuZhCompany
from .xueqiu_stock_quote import XueqiuStockQuote

logger = logging.getLogger(__name__)


class XueqiuApi:
    """雪球API - 重构版本"""

    def __init__(self):
        """初始化雪球API，使用重构后的股票客户端"""
        # 使用新的客户端工厂创建股票客户端
        self._client = create_stock_client()
        logger.info("雪球API初始化完成（使用重构后的客户端）")

    def get_stock_quote(self, code: str) -> Optional[XueqiuStockQuote]:
        """获取股票状态"""
        return self._client.get_stock_quote(code)

    def get_zh_stock_company(self, code: str) -> Optional[XueqiuZhCompany]:
        """获取A股公司详情"""
        return self._client.get_zh_stock_company(code)

    def get_hk_stock_company(self, code: str) -> Optional[XueqiuHkCompany]:
        """获取港股公司详情"""
        return self._client.get_hk_stock_company(code)

    def get_us_stock_company(self, code: str) -> Optional[XueqiuUsCompany]:
        """获取美股公司详情"""
        return self._client.get_us_stock_company(code)

    def get_stock_history(self, code: str, start_date: str) -> Optional[pd.DataFrame]:
        """获取股票历史数据"""
        return self._client.get_stock_history(code, start_date)

    # 异步版本的方法
    async def get_stock_quote_async(self, code: str) -> Optional[XueqiuStockQuote]:
        """异步获取股票状态"""
        async with create_stock_client() as client:
            return await client.get_stock_quote_async(code)

    async def get_zh_stock_company_async(self, code: str) -> Optional[XueqiuZhCompany]:
        """异步获取A股公司详情"""
        async with create_stock_client() as client:
            return await client.get_zh_stock_company_async(code)

    async def get_hk_stock_company_async(self, code: str) -> Optional[XueqiuHkCompany]:
        """异步获取港股公司详情"""
        async with create_stock_client() as client:
            return await client.get_hk_stock_company_async(code)

    async def get_us_stock_company_async(self, code: str) -> Optional[XueqiuUsCompany]:
        """异步获取美股公司详情"""
        async with create_stock_client() as client:
            return await client.get_us_stock_company_async(code)

    # 保留一些向后兼容的低级别方法
    def _get_token_with_urllib(self):
        """使用urllib获取雪球token（向后兼容方法）"""
        return self._client._get_token_with_urllib()

    async def _get_token_with_puppeteer(self) -> Optional[str]:
        """使用pyppeteer获取雪球的token（向后兼容方法）"""
        return await self._client._get_token_with_puppeteer()

    def _get_token(self):
        """获取雪球token（向后兼容方法）"""
        logger.warning("_get_token方法已废弃，请使用新的客户端抽象层")
        # 尝试从客户端获取token
        if hasattr(self._client, "xqat") and self._client.xqat:
            return True

        # 如果没有token，尝试获取
        token = self._client._get_token_with_urllib()
        if token:
            self._client.xqat = token
            return True
        return False

    def _request(self, url, retry=True):
        """发送HTTP请求（向后兼容方法）"""
        logger.warning("_request方法已废弃，请使用新的客户端抽象层")
        return self._client._sync_request(url, retry)

    def _get_symbol(self, code):
        """转化股票代码（向后兼容方法）"""
        return self._client._get_symbol(code)
