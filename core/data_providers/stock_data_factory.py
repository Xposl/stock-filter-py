"""
股票数据工厂
实现策略模式，统一管理多个股票数据提供者，支持智能降级和负载均衡
"""

import logging
from datetime import date, datetime
from typing import Any, Optional, Union

from .akshare_industry_provider import AKShareIndustryProvider
from .akshare_provider import AKShareProvider
from .stock_data_provider import (
    DataPeriod,
    StockDataProvider,
    StockDataResponse,
    StockMarket,
)
from .xueqiu_provider import XueqiuProvider

logger = logging.getLogger(__name__)


class StockDataFactory:
    """股票数据工厂"""

    def __init__(self):
        """初始化股票数据工厂"""
        self._providers: list[StockDataProvider] = []
        self._provider_cache: dict[str, StockDataProvider] = {}
        self._industry_provider: Optional[AKShareIndustryProvider] = None
        self._initialize_providers()

    def _initialize_providers(self):
        """初始化数据提供者"""
        try:
            # 添加AKShare提供者（优先级最高）
            akshare_provider = AKShareProvider()
            self.add_provider(akshare_provider)
            logger.info("已添加AKShare数据提供者")

            # 添加雪球提供者（作为补充）
            xueqiu_provider = XueqiuProvider()
            self.add_provider(xueqiu_provider)
            logger.info("已添加雪球数据提供者")

            # 添加AKShare行业提供者（专门用于行业数据）
            self._industry_provider = AKShareIndustryProvider()
            logger.info("已添加AKShare行业数据提供者")

        except Exception as e:
            logger.error(f"初始化数据提供者失败: {e}")

    def add_provider(self, provider: StockDataProvider):
        """
        添加数据提供者

        Args:
            provider: 数据提供者实例
        """
        if not isinstance(provider, StockDataProvider):
            raise ValueError("提供者必须继承自StockDataProvider")

        self._providers.append(provider)
        self._provider_cache[provider.name] = provider

        # 按优先级排序
        self._providers.sort(key=lambda p: p.priority, reverse=True)

        logger.info(f"已添加数据提供者: {provider.name} (优先级: {provider.priority})")

    def remove_provider(self, provider_name: str):
        """
        移除数据提供者

        Args:
            provider_name: 提供者名称
        """
        if provider_name in self._provider_cache:
            provider = self._provider_cache[provider_name]
            self._providers.remove(provider)
            del self._provider_cache[provider_name]
            logger.info(f"已移除数据提供者: {provider_name}")

    def get_provider(self, provider_name: str) -> Optional[StockDataProvider]:
        """
        获取指定的数据提供者

        Args:
            provider_name: 提供者名称

        Returns:
            数据提供者实例或None
        """
        return self._provider_cache.get(provider_name)

    def get_available_providers(self) -> list[StockDataProvider]:
        """
        获取可用的数据提供者列表

        Returns:
            可用的数据提供者列表
        """
        return [p for p in self._providers if p.is_available]

    def _select_best_provider(
        self, operation: str, market: StockMarket = None
    ) -> Optional[StockDataProvider]:
        """
        选择最佳的数据提供者

        Args:
            operation: 操作类型
            market: 市场类型

        Returns:
            最佳的数据提供者或None
        """
        available_providers = self.get_available_providers()

        if not available_providers:
            logger.error("没有可用的数据提供者")
            return None

        # 如果指定了市场，优先选择支持该市场的提供者
        if market:
            market_providers = [
                p for p in available_providers if market in p.get_supported_markets()
            ]
            if market_providers:
                return market_providers[0]  # 返回优先级最高的

        # 返回优先级最高的可用提供者
        return available_providers[0]

    def get_stock_info(
        self, symbol: str, market: StockMarket = None, provider_name: str = None
    ) -> StockDataResponse:
        """
        获取股票基本信息

        Args:
            symbol: 股票代码
            market: 市场类型
            provider_name: 指定的提供者名称

        Returns:
            股票数据响应
        """
        if provider_name:
            provider = self.get_provider(provider_name)
            if provider and provider.is_available:
                try:
                    data = provider.get_stock_info(symbol, market)
                    return StockDataResponse(data, provider.name, data is not None)
                except Exception as e:
                    logger.error(f"指定提供者 {provider_name} 获取股票信息失败: {e}")
                    return StockDataResponse(None, provider_name, False, str(e))

        # 自动选择最佳提供者
        for provider in self.get_available_providers():
            if market and market not in provider.get_supported_markets():
                continue

            try:
                data = provider.get_stock_info(symbol, market)
                if data:
                    return StockDataResponse(data, provider.name, True)
                else:
                    logger.warning(f"提供者 {provider.name} 未找到股票信息: {symbol}")
            except Exception as e:
                logger.error(f"提供者 {provider.name} 获取股票信息失败: {e}")
                provider._handle_error(e, "获取股票信息")

        return StockDataResponse(None, "None", False, "所有提供者均失败")

    def get_stock_quote(
        self, symbol: str, market: StockMarket = None, provider_name: str = None
    ) -> StockDataResponse:
        """
        获取股票实时行情

        Args:
            symbol: 股票代码
            market: 市场类型
            provider_name: 指定的提供者名称

        Returns:
            股票数据响应
        """
        if provider_name:
            provider = self.get_provider(provider_name)
            if provider and provider.is_available:
                try:
                    data = provider.get_stock_quote(symbol, market)
                    return StockDataResponse(data, provider.name, data is not None)
                except Exception as e:
                    logger.error(f"指定提供者 {provider_name} 获取股票行情失败: {e}")
                    return StockDataResponse(None, provider_name, False, str(e))

        # 自动选择最佳提供者
        for provider in self.get_available_providers():
            if market and market not in provider.get_supported_markets():
                continue

            try:
                data = provider.get_stock_quote(symbol, market)
                if data:
                    return StockDataResponse(data, provider.name, True)
                else:
                    logger.warning(f"提供者 {provider.name} 未找到股票行情: {symbol}")
            except Exception as e:
                logger.error(f"提供者 {provider.name} 获取股票行情失败: {e}")
                provider._handle_error(e, "获取股票行情")

        return StockDataResponse(None, "None", False, "所有提供者均失败")

    def get_stock_history(
        self,
        symbol: str,
        start_date: Union[str, date, datetime],
        end_date: Union[str, date, datetime] = None,
        period: DataPeriod = DataPeriod.DAILY,
        market: StockMarket = None,
        provider_name: str = None,
    ) -> StockDataResponse:
        """
        获取股票历史数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            period: 数据周期
            market: 市场类型
            provider_name: 指定的提供者名称

        Returns:
            股票数据响应
        """
        if provider_name:
            provider = self.get_provider(provider_name)
            if provider and provider.is_available:
                try:
                    data = provider.get_stock_history(
                        symbol, start_date, end_date, period, market
                    )
                    return StockDataResponse(data, provider.name, data is not None)
                except Exception as e:
                    logger.error(f"指定提供者 {provider_name} 获取历史数据失败: {e}")
                    return StockDataResponse(None, provider_name, False, str(e))

        # 自动选择最佳提供者
        for provider in self.get_available_providers():
            if market and market not in provider.get_supported_markets():
                continue

            try:
                data = provider.get_stock_history(
                    symbol, start_date, end_date, period, market
                )
                if data is not None and not data.empty:
                    return StockDataResponse(data, provider.name, True)
                else:
                    logger.warning(f"提供者 {provider.name} 未找到历史数据: {symbol}")
            except Exception as e:
                logger.error(f"提供者 {provider.name} 获取历史数据失败: {e}")
                provider._handle_error(e, "获取历史数据")

        return StockDataResponse(None, "None", False, "所有提供者均失败")

    def get_company_info(
        self, symbol: str, market: StockMarket = None, provider_name: str = None
    ) -> StockDataResponse:
        """
        获取公司详细信息

        Args:
            symbol: 股票代码
            market: 市场类型
            provider_name: 指定的提供者名称

        Returns:
            股票数据响应
        """
        if provider_name:
            provider = self.get_provider(provider_name)
            if provider and provider.is_available:
                try:
                    data = provider.get_company_info(symbol, market)
                    return StockDataResponse(data, provider.name, data is not None)
                except Exception as e:
                    logger.error(f"指定提供者 {provider_name} 获取公司信息失败: {e}")
                    return StockDataResponse(None, provider_name, False, str(e))

        # 自动选择最佳提供者
        for provider in self.get_available_providers():
            if market and market not in provider.get_supported_markets():
                continue

            try:
                data = provider.get_company_info(symbol, market)
                if data:
                    return StockDataResponse(data, provider.name, True)
                else:
                    logger.warning(f"提供者 {provider.name} 未找到公司信息: {symbol}")
            except Exception as e:
                logger.error(f"提供者 {provider.name} 获取公司信息失败: {e}")
                provider._handle_error(e, "获取公司信息")

        return StockDataResponse(None, "None", False, "所有提供者均失败")

    def search_stocks(
        self,
        keyword: str,
        market: StockMarket = None,
        limit: int = 10,
        provider_name: str = None,
    ) -> StockDataResponse:
        """
        搜索股票

        Args:
            keyword: 搜索关键词
            market: 市场类型
            limit: 返回结果数量限制
            provider_name: 指定的提供者名称

        Returns:
            股票数据响应
        """
        if provider_name:
            provider = self.get_provider(provider_name)
            if provider and provider.is_available:
                try:
                    data = provider.search_stocks(keyword, market, limit)
                    return StockDataResponse(data, provider.name, len(data) > 0)
                except Exception as e:
                    logger.error(f"指定提供者 {provider_name} 搜索股票失败: {e}")
                    return StockDataResponse([], provider_name, False, str(e))

        # 自动选择最佳提供者
        for provider in self.get_available_providers():
            if market and market not in provider.get_supported_markets():
                continue

            try:
                data = provider.search_stocks(keyword, market, limit)
                if data:
                    return StockDataResponse(data, provider.name, True)
            except Exception as e:
                logger.error(f"提供者 {provider.name} 搜索股票失败: {e}")
                provider._handle_error(e, "搜索股票")

        return StockDataResponse([], "None", False, "所有提供者均失败")

    def reset_providers(self):
        """重置所有提供者的错误计数"""
        for provider in self._providers:
            provider.reset_error_count()
        logger.info("已重置所有提供者的错误计数")

    def get_provider_status(self) -> dict[str, dict[str, Any]]:
        """
        获取所有提供者的状态

        Returns:
            提供者状态字典
        """
        status = {}
        for provider in self._providers:
            status[provider.name] = {
                "priority": provider.priority,
                "is_available": provider.is_available,
                "error_count": provider._error_count,
                "supported_markets": [
                    market.value for market in provider.get_supported_markets()
                ],
            }
        return status

    async def get_industry_stocks(
        self,
        industry: str,
        impact_type: str = "positive",
        impact_degree: int = 5,
        limit: int = 10,
    ) -> list[dict]:
        """
        获取特定行业的代表性股票

        Args:
            industry: 行业名称
            impact_type: 影响类型
            impact_degree: 影响程度 (1-10)
            limit: 返回股票数量限制

        Returns:
            股票列表
        """
        if self._industry_provider and self._industry_provider.is_available:
            try:
                return await self._industry_provider.get_industry_stocks(
                    industry, impact_type, impact_degree, limit
                )
            except Exception as e:
                logger.error(f"获取行业股票失败: {e}")
                return []
        else:
            logger.warning("行业数据提供者不可用")
            return []

    async def get_all_industry_categories(self) -> dict[str, list[str]]:
        """
        获取全市场的行业分类体系

        Returns:
            行业分类字典
        """
        if self._industry_provider and self._industry_provider.is_available:
            try:
                return await self._industry_provider.get_all_industry_categories()
            except Exception as e:
                logger.error(f"获取行业分类失败: {e}")
                return {}
        else:
            logger.warning("行业数据提供者不可用")
            return {}

    def get_industry_provider(self) -> Optional[AKShareIndustryProvider]:
        """获取行业数据提供者"""
        return self._industry_provider


# 全局工厂实例
_default_factory: Optional[StockDataFactory] = None


def get_stock_data_factory() -> StockDataFactory:
    """获取全局股票数据工厂实例"""
    global _default_factory
    if _default_factory is None:
        _default_factory = StockDataFactory()
    return _default_factory


# 便捷函数
def get_stock_info(
    symbol: str, market: StockMarket = None, provider_name: str = None
) -> StockDataResponse:
    """获取股票基本信息的便捷函数"""
    return get_stock_data_factory().get_stock_info(symbol, market, provider_name)


def get_stock_quote(
    symbol: str, market: StockMarket = None, provider_name: str = None
) -> StockDataResponse:
    """获取股票实时行情的便捷函数"""
    return get_stock_data_factory().get_stock_quote(symbol, market, provider_name)


def get_stock_history(
    symbol: str,
    start_date: Union[str, date, datetime],
    end_date: Union[str, date, datetime] = None,
    period: DataPeriod = DataPeriod.DAILY,
    market: StockMarket = None,
    provider_name: str = None,
) -> StockDataResponse:
    """获取股票历史数据的便捷函数"""
    return get_stock_data_factory().get_stock_history(
        symbol, start_date, end_date, period, market, provider_name
    )


def get_company_info(
    symbol: str, market: StockMarket = None, provider_name: str = None
) -> StockDataResponse:
    """获取公司详细信息的便捷函数"""
    return get_stock_data_factory().get_company_info(symbol, market, provider_name)


def search_stocks(
    keyword: str, market: StockMarket = None, limit: int = 10, provider_name: str = None
) -> StockDataResponse:
    """便捷函数：搜索股票"""
    return get_stock_data_factory().search_stocks(keyword, market, limit, provider_name)


# 新增：行业数据获取便捷函数
async def get_industry_stocks(
    industry: str,
    impact_type: str = "positive",
    impact_degree: int = 5,
    limit: int = 10,
) -> list[dict]:
    """便捷函数：获取行业股票"""
    return await get_stock_data_factory().get_industry_stocks(
        industry, impact_type, impact_degree, limit
    )


async def get_all_industry_categories() -> dict[str, list[str]]:
    """便捷函数：获取全市场行业分类"""
    return await get_stock_data_factory().get_all_industry_categories()


def get_industry_provider() -> Optional[AKShareIndustryProvider]:
    """便捷函数：获取行业数据提供者"""
    return get_stock_data_factory().get_industry_provider()
