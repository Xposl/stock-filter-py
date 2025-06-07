"""
雪球股票数据提供者
基于雪球API实现的股票数据获取，作为AKShare的补充数据源
"""

import logging
from datetime import date, datetime
from typing import Any, Optional, Union

import pandas as pd

from ..utils.xueqiu.xueqiu_client_factory import create_stock_client
from .stock_data_provider import DataPeriod, StockDataProvider, StockMarket

logger = logging.getLogger(__name__)


class XueqiuProvider(StockDataProvider):
    """雪球数据提供者"""

    def __init__(self):
        super().__init__(name="雪球", priority=50)  # 中等优先级，作为补充数据源
        self._supported_markets = [
            StockMarket.A_SHARE,
            StockMarket.HONG_KONG,
            StockMarket.US,
        ]
        self._client = create_stock_client()

    def get_supported_markets(self) -> list[StockMarket]:
        """获取支持的市场列表"""
        return self._supported_markets

    def normalize_symbol(self, symbol: str, market: StockMarket = None) -> str:
        """标准化股票代码"""
        symbol = symbol.upper().strip()

        # 雪球的股票代码格式化
        if market == StockMarket.A_SHARE:
            if symbol.startswith("SH") or symbol.startswith("SZ"):
                return symbol  # 已经是雪球格式
            elif symbol.isdigit() and len(symbol) == 6:
                # 判断是上海还是深圳
                if symbol.startswith("6"):
                    return f"SH{symbol}"
                else:
                    return f"SZ{symbol}"
        elif market == StockMarket.HONG_KONG:
            if not symbol.startswith("HK"):
                return f"HK{symbol.zfill(5)}"
        elif market == StockMarket.US:
            # 美股直接使用代码
            return symbol

        return symbol

    def _detect_market(self, symbol: str) -> StockMarket:
        """自动检测股票市场"""
        symbol = symbol.upper().strip()

        # A股检测
        if symbol.startswith("SH") or symbol.startswith("SZ"):
            return StockMarket.A_SHARE
        elif symbol.isdigit() and len(symbol) == 6:
            return StockMarket.A_SHARE

        # 港股检测
        elif symbol.startswith("HK") or (symbol.isdigit() and len(symbol) <= 5):
            return StockMarket.HONG_KONG

        # 美股检测
        elif symbol.isalpha():
            return StockMarket.US

        return StockMarket.OTHER

    def get_stock_info(
        self, symbol: str, market: StockMarket = None
    ) -> Optional[dict[str, Any]]:
        """获取股票基本信息"""
        try:
            if market is None:
                market = self._detect_market(symbol)

            symbol = self.normalize_symbol(symbol, market)

            # 使用雪球客户端获取股票报价信息
            quote = self._client.get_stock_quote(symbol)

            if quote is None:
                return None

            # 转换为标准格式
            stock_quote = quote.quote
            return {
                "symbol": stock_quote.symbol,
                "name": stock_quote.name,
                "market": self._get_market_name(market),
                "current_price": stock_quote.current,
                "change_percent": stock_quote.percent,
                "volume": stock_quote.volume,
                "turnover": stock_quote.amount,
                "pe_ratio": stock_quote.pe_ttm,
                "pb_ratio": stock_quote.pb,
                "total_value": stock_quote.market_capital,
                "circulation_value": stock_quote.float_market_capital,
            }

        except Exception as e:
            self._handle_error(e, "获取股票基本信息")
            return None

    def get_stock_quote(
        self, symbol: str, market: StockMarket = None
    ) -> Optional[dict[str, Any]]:
        """获取股票实时行情"""
        try:
            if market is None:
                market = self._detect_market(symbol)

            symbol = self.normalize_symbol(symbol, market)

            # 使用雪球客户端获取股票报价
            quote = self._client.get_stock_quote(symbol)

            if quote is None:
                return None

            stock_quote = quote.quote
            return {
                "symbol": stock_quote.symbol,
                "name": stock_quote.name,
                "current": stock_quote.current,
                "open": stock_quote.open,
                "close": stock_quote.last_close,
                "high": stock_quote.high,
                "low": stock_quote.low,
                "volume": stock_quote.volume,
                "amount": stock_quote.amount,
                "change": stock_quote.chg,
                "change_percent": stock_quote.percent,
                "turnover_rate": stock_quote.turnover_rate,
                "pe_ratio": stock_quote.pe_ttm,
                "pb_ratio": stock_quote.pb,
                "timestamp": datetime.now(),
            }

        except Exception as e:
            self._handle_error(e, "获取股票实时行情")
            return None

    def get_stock_history(
        self,
        symbol: str,
        start_date: Union[str, date, datetime],
        end_date: Union[str, date, datetime] = None,
        period: DataPeriod = DataPeriod.DAILY,
        market: StockMarket = None,
    ) -> Optional[pd.DataFrame]:
        """获取股票历史数据"""
        try:
            if market is None:
                market = self._detect_market(symbol)

            symbol = self.normalize_symbol(symbol, market)

            # 格式化开始日期
            if isinstance(start_date, (date, datetime)):
                start_date_str = start_date.strftime("%Y-%m-%d")
            else:
                start_date_str = start_date

            # 雪球目前主要支持日线数据
            if period != DataPeriod.DAILY:
                logger.warning(f"雪球提供者目前仅支持日线数据，当前请求周期: {period}")

            # 使用雪球客户端获取历史数据
            df = self._client.get_stock_history(symbol, start_date_str)

            if df is None or df.empty:
                return None

            # 标准化列名
            df_standard = pd.DataFrame()
            df_standard["open"] = df["open"]
            df_standard["high"] = df["high"]
            df_standard["low"] = df["low"]
            df_standard["close"] = df["close"]
            df_standard["volume"] = df["volume"]

            if "change_rate" in df.columns:
                df_standard["change_percent"] = df["change_rate"]
            if "turnover_rate" in df.columns:
                df_standard["turnover"] = df["turnover_rate"]

            df_standard.index = df.index

            return df_standard

        except Exception as e:
            self._handle_error(e, "获取股票历史数据")
            return None

    def get_company_info(
        self, symbol: str, market: StockMarket = None
    ) -> Optional[dict[str, Any]]:
        """获取公司详细信息"""
        try:
            if market is None:
                market = self._detect_market(symbol)

            symbol = self.normalize_symbol(symbol, market)

            # 根据市场类型调用不同的方法
            if market == StockMarket.A_SHARE:
                company = self._client.get_zh_stock_company(symbol)
            elif market == StockMarket.HONG_KONG:
                company = self._client.get_hk_stock_company(symbol)
            elif market == StockMarket.US:
                company = self._client.get_us_stock_company(symbol)
            else:
                return None

            if company is None:
                return None

            # 标准化公司信息
            return {
                "symbol": symbol,
                "name": company.company_name,
                "industry": getattr(company, "industry", None),
                "market_cap": getattr(company, "market_capital", None),
                "pe_ratio": getattr(company, "pe_ttm", None),
                "pb_ratio": getattr(company, "pb", None),
                "website": getattr(company, "website", None),
                "business_scope": getattr(company, "business_scope", None),
                "introduction": getattr(company, "introduction", None),
                "listing_date": getattr(company, "listing_date", None),
                "employees": getattr(company, "employees", None),
            }

        except Exception as e:
            self._handle_error(e, "获取公司详细信息")
            return None

    def search_stocks(
        self, keyword: str, market: StockMarket = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        """搜索股票"""
        try:
            # 雪球没有直接的搜索API，这里返回空列表
            # 在实际使用中，会优先使用AKShare的搜索功能
            logger.info("雪球提供者暂不支持股票搜索，请使用AKShare提供者")
            return []

        except Exception as e:
            self._handle_error(e, "搜索股票")
            return []

    def _get_market_name(self, market: StockMarket) -> str:
        """获取市场中文名称"""
        market_names = {
            StockMarket.A_SHARE: "A股",
            StockMarket.HONG_KONG: "港股",
            StockMarket.US: "美股",
            StockMarket.UK: "英股",
            StockMarket.OTHER: "其他",
        }
        return market_names.get(market, "未知")

    async def get_stock_quote_async(
        self, symbol: str, market: StockMarket = None
    ) -> Optional[dict[str, Any]]:
        """异步获取股票实时行情"""
        try:
            if market is None:
                market = self._detect_market(symbol)

            symbol = self.normalize_symbol(symbol, market)

            # 使用异步雪球客户端
            quote = await self._client.get_stock_quote_async(symbol)

            if quote is None:
                return None

            stock_quote = quote.quote
            return {
                "symbol": stock_quote.symbol,
                "name": stock_quote.name,
                "current": stock_quote.current,
                "open": stock_quote.open,
                "close": stock_quote.last_close,
                "high": stock_quote.high,
                "low": stock_quote.low,
                "volume": stock_quote.volume,
                "amount": stock_quote.amount,
                "change": stock_quote.chg,
                "change_percent": stock_quote.percent,
                "turnover_rate": stock_quote.turnover_rate,
                "pe_ratio": stock_quote.pe_ttm,
                "pb_ratio": stock_quote.pb,
                "timestamp": datetime.now(),
            }

        except Exception as e:
            self._handle_error(e, "异步获取股票实时行情")
            return None
