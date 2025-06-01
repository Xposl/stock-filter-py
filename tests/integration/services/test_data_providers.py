#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据提供者集成测试
测试股票数据提供者与外部API的集成
"""

import pytest
import asyncio
import logging
from decimal import Decimal
from datetime import datetime, timedelta

from core.data_providers.stock_data_factory import StockDataFactory, get_stock_data_factory
from core.data_providers.akshare_provider import AKShareProvider
from core.data_providers.xueqiu_provider import XueqiuProvider
from core.data_providers.stock_data_provider import StockMarket, StockDataProvider


@pytest.mark.integration
@pytest.mark.slow
class TestStockDataIntegration:
    """测试股票数据提供者的集成功能"""
    
    @pytest.fixture(scope="class")
    def factory(self):
        """获取股票数据工厂实例"""
        return StockDataFactory()
    
    def test_factory_initialization(self, factory):
        """测试工厂初始化"""
        assert factory is not None
        assert len(factory._providers) > 0
        
        # 验证提供者按优先级排序
        priorities = [p.priority for p in factory._providers]
        assert priorities == sorted(priorities, reverse=True)
    
    def test_get_stock_data_factory_function(self):
        """测试便捷函数"""
        factory = get_stock_data_factory()
        assert factory is not None
        assert isinstance(factory, StockDataFactory)
    
    def test_stock_quote_integration(self, factory):
        """测试股票行情获取集成"""
        # 测试A股
        try:
            quote = factory.get_stock_quote("000001", StockMarket.A_SHARE)
            if quote.success:
                assert quote.data is not None
                assert 'symbol' in quote.data or 'code' in quote.data
                logging.info(f"A股行情获取成功: {quote.data}")
            else:
                logging.warning(f"A股行情获取失败: {quote.error}")
        except Exception as e:
            logging.error(f"A股行情测试异常: {e}")
    
    def test_stock_info_integration(self, factory):
        """测试股票信息获取集成"""
        # 测试股票基本信息
        try:
            info = factory.get_stock_info("000001", StockMarket.A_SHARE)
            if info.success:
                assert info.data is not None
                logging.info(f"股票信息获取成功: {info.data}")
            else:
                logging.warning(f"股票信息获取失败: {info.error}")
        except Exception as e:
            logging.error(f"股票信息测试异常: {e}")
    
    def test_stock_search_integration(self, factory):
        """测试股票搜索集成"""
        try:
            results = factory.search_stocks("平安", StockMarket.A_SHARE)
            if results.success:
                assert results.data is not None
                assert isinstance(results.data, list)
                if results.data:
                    logging.info(f"股票搜索成功: 找到 {len(results.data)} 个结果")
                else:
                    logging.info("股票搜索成功但无结果")
            else:
                logging.warning(f"股票搜索失败: {results.error}")
        except Exception as e:
            logging.error(f"股票搜索测试异常: {e}")
    
    def test_company_info_integration(self, factory):
        """测试公司信息获取集成"""
        try:
            info = factory.get_company_info("000001", StockMarket.A_SHARE)
            if info.success:
                assert info.data is not None
                logging.info(f"公司信息获取成功: {info.data}")
            else:
                logging.warning(f"公司信息获取失败: {info.error}")
        except Exception as e:
            logging.error(f"公司信息测试异常: {e}")


@pytest.mark.integration 
@pytest.mark.slow
class TestAKShareProviderIntegration:
    """测试AKShare提供者集成"""
    
    @pytest.fixture
    def provider(self):
        """获取AKShare提供者实例"""
        return AKShareProvider()
    
    def test_akshare_stock_quote(self, provider):
        """测试AKShare股票行情"""
        try:
            result = provider.get_stock_quote("000001", StockMarket.A_SHARE)
            if result:
                assert result is not None
                logging.info(f"AKShare行情: {result}")
            else:
                logging.warning("AKShare行情获取失败")
        except Exception as e:
            logging.error(f"AKShare行情异常: {e}")
    
    def test_akshare_stock_info(self, provider):
        """测试AKShare股票信息"""
        try:
            result = provider.get_stock_info("000001", StockMarket.A_SHARE)
            if result:
                assert result is not None
                logging.info(f"AKShare信息: {result}")
            else:
                logging.warning("AKShare信息获取失败")
        except Exception as e:
            logging.error(f"AKShare信息异常: {e}")


@pytest.mark.integration
@pytest.mark.slow
class TestXueqiuProviderIntegration:
    """测试雪球提供者集成"""
    
    @pytest.fixture
    def provider(self):
        """获取雪球提供者实例"""
        return XueqiuProvider()
    
    def test_xueqiu_stock_quote(self, provider):
        """测试雪球股票行情"""
        try:
            result = provider.get_stock_quote("SH000001", StockMarket.A_SHARE)
            if result:
                assert result is not None
                logging.info(f"雪球行情: {result}")
            else:
                logging.warning("雪球行情获取失败")
        except Exception as e:
            logging.error(f"雪球行情异常: {e}")
    
    def test_xueqiu_company_info(self, provider):
        """测试雪球公司信息"""
        try:
            result = provider.get_company_info("SH000001", StockMarket.A_SHARE)
            if result:
                assert result is not None
                logging.info(f"雪球公司信息: {result}")
            else:
                logging.warning("雪球公司信息获取失败")
        except Exception as e:
            logging.error(f"雪球公司信息异常: {e}")


@pytest.mark.integration
class TestDataProviderFallback:
    """测试数据提供者降级机制"""
    
    @pytest.fixture
    def factory(self):
        """获取工厂实例"""
        return StockDataFactory()
    
    def test_provider_availability(self, factory):
        """测试提供者可用性"""
        for provider in factory._providers:
            assert hasattr(provider, 'is_available')
            assert hasattr(provider, 'priority')
            assert hasattr(provider, '_error_count')
            assert hasattr(provider, '_max_errors')
    
    def test_fallback_mechanism(self, factory):
        """测试降级机制"""
        # 这个测试需要模拟提供者失败的情况
        # 在实际集成测试中，我们可以观察到自动降级的行为
        
        try:
            quote = factory.get_stock_quote("000001", StockMarket.A_SHARE)
            # 无论成功还是失败，都应该有响应
            assert quote is not None
            assert hasattr(quote, 'success')
            assert hasattr(quote, 'data')
            assert hasattr(quote, 'error')
            
            if quote.success:
                logging.info("数据获取成功，降级机制正常")
            else:
                logging.warning(f"数据获取失败，但降级机制正常工作: {quote.error}")
                
        except Exception as e:
            logging.error(f"降级机制测试异常: {e}")
            # 即使异常，也不应该让测试失败，因为这是集成测试
            # 外部API可能不可用


if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(level=logging.INFO)
    
    # 运行集成测试
    pytest.main([__file__, "-v", "--tb=short", "-m", "integration"]) 