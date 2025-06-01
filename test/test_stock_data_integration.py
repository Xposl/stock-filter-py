#!/usr/bin/env python3
"""
测试股票数据集成功能
验证AKShare和雪球数据源的集成和策略选择
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.data_providers.stock_data_factory import (
    get_stock_data_factory, 
    get_stock_info, 
    get_stock_quote, 
    get_stock_history,
    search_stocks
)
from core.data_providers.stock_data_provider import StockMarket, DataPeriod

import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_factory_initialization():
    """测试工厂初始化"""
    print("=" * 50)
    print("测试工厂初始化")
    print("=" * 50)
    
    factory = get_stock_data_factory()
    
    # 获取提供者状态
    status = factory.get_provider_status()
    print("数据提供者状态:")
    for name, info in status.items():
        print(f"  {name}: 优先级={info['priority']}, 可用={info['is_available']}, 支持市场={info['supported_markets']}")
    
    print(f"\n可用提供者数量: {len(factory.get_available_providers())}")


def test_akshare_a_share():
    """测试AKShare A股数据"""
    print("=" * 50)
    print("测试AKShare A股数据")
    print("=" * 50)
    
    symbol = "000001"  # 平安银行
    
    # 测试股票基本信息
    print(f"获取 {symbol} 基本信息...")
    info_response = get_stock_info(symbol, StockMarket.A_SHARE, "AKShare")
    if info_response:
        print(f"  提供者: {info_response.provider}")
        print(f"  股票名称: {info_response.data.get('name')}")
        print(f"  当前价格: {info_response.data.get('current_price')}")
        print(f"  涨跌幅: {info_response.data.get('change_percent')}%")
    else:
        print(f"  获取失败: {info_response.error}")
    
    # 测试实时行情
    print(f"\n获取 {symbol} 实时行情...")
    quote_response = get_stock_quote(symbol, StockMarket.A_SHARE, "AKShare")
    if quote_response:
        print(f"  提供者: {quote_response.provider}")
        print(f"  当前价: {quote_response.data.get('current')}")
        print(f"  开盘价: {quote_response.data.get('open')}")
        print(f"  最高价: {quote_response.data.get('high')}")
        print(f"  最低价: {quote_response.data.get('low')}")
        print(f"  成交量: {quote_response.data.get('volume')}")
    else:
        print(f"  获取失败: {quote_response.error}")
    
    # 测试历史数据
    print(f"\n获取 {symbol} 历史数据...")
    history_response = get_stock_history(
        symbol, 
        "2024-01-01", 
        "2024-01-31", 
        DataPeriod.DAILY, 
        StockMarket.A_SHARE, 
        "AKShare"
    )
    if history_response:
        print(f"  提供者: {history_response.provider}")
        print(f"  数据行数: {len(history_response.data)}")
        print(f"  数据列: {list(history_response.data.columns)}")
        print(f"  最新5行数据:")
        print(history_response.data.tail())
    else:
        print(f"  获取失败: {history_response.error}")


def test_automatic_provider_selection():
    """测试自动提供者选择"""
    print("=" * 50)
    print("测试自动提供者选择")
    print("=" * 50)
    
    symbol = "000001"
    
    # 不指定提供者，让系统自动选择
    print(f"自动选择提供者获取 {symbol} 信息...")
    info_response = get_stock_info(symbol, StockMarket.A_SHARE)
    if info_response:
        print(f"  选择的提供者: {info_response.provider}")
        print(f"  股票名称: {info_response.data.get('name')}")
        print(f"  当前价格: {info_response.data.get('current_price')}")
    else:
        print(f"  获取失败: {info_response.error}")


def test_stock_search():
    """测试股票搜索"""
    print("=" * 50)
    print("测试股票搜索")
    print("=" * 50)
    
    keyword = "平安"
    
    print(f"搜索关键词: {keyword}")
    search_response = search_stocks(keyword, StockMarket.A_SHARE, 5)
    if search_response:
        print(f"  提供者: {search_response.provider}")
        print(f"  找到 {len(search_response.data)} 个结果:")
        for stock in search_response.data:
            print(f"    {stock['symbol']} - {stock['name']} ({stock['market']})")
    else:
        print(f"  搜索失败: {search_response.error}")


def test_provider_fallback():
    """测试提供者降级"""
    print("=" * 50)
    print("测试提供者降级")
    print("=" * 50)
    
    factory = get_stock_data_factory()
    
    # 模拟AKShare提供者不可用
    akshare_provider = factory.get_provider("AKShare")
    if akshare_provider:
        print("临时禁用AKShare提供者...")
        akshare_provider._is_available = False
    
    symbol = "SH600000"  # 浦发银行
    
    print(f"获取 {symbol} 信息（AKShare不可用）...")
    info_response = get_stock_info(symbol, StockMarket.A_SHARE)
    if info_response:
        print(f"  降级到提供者: {info_response.provider}")
        print(f"  股票名称: {info_response.data.get('name')}")
    else:
        print(f"  获取失败: {info_response.error}")
    
    # 恢复AKShare提供者
    if akshare_provider:
        print("恢复AKShare提供者...")
        akshare_provider._is_available = True


def test_multiple_markets():
    """测试多市场支持"""
    print("=" * 50)
    print("测试多市场支持")
    print("=" * 50)
    
    # A股
    print("A股测试:")
    a_response = get_stock_info("000001", StockMarket.A_SHARE)
    if a_response:
        print(f"  {a_response.data.get('symbol')} - {a_response.data.get('name')} (提供者: {a_response.provider})")
    
    # 港股（如果可用）
    print("\n港股测试:")
    try:
        hk_response = get_stock_info("00700", StockMarket.HONG_KONG)
        if hk_response:
            print(f"  {hk_response.data.get('symbol')} - {hk_response.data.get('name')} (提供者: {hk_response.provider})")
        else:
            print("  港股数据不可用")
    except Exception as e:
        print(f"  港股测试失败: {e}")
    
    # 美股（如果可用）
    print("\n美股测试:")
    try:
        us_response = get_stock_info("AAPL", StockMarket.US)
        if us_response:
            print(f"  {us_response.data.get('symbol')} - {us_response.data.get('name')} (提供者: {us_response.provider})")
        else:
            print("  美股数据不可用")
    except Exception as e:
        print(f"  美股测试失败: {e}")


async def test_xueqiu_integration():
    """测试雪球集成"""
    print("=" * 50)
    print("测试雪球集成")
    print("=" * 50)
    
    symbol = "SH600000"
    
    try:
        # 强制使用雪球提供者
        print(f"使用雪球提供者获取 {symbol} 信息...")
        info_response = get_stock_info(symbol, StockMarket.A_SHARE, "雪球")
        if info_response:
            print(f"  提供者: {info_response.provider}")
            print(f"  股票名称: {info_response.data.get('name')}")
            print(f"  当前价格: {info_response.data.get('current_price')}")
            print(f"  市盈率: {info_response.data.get('pe_ratio')}")
        else:
            print(f"  获取失败: {info_response.error}")
    except Exception as e:
        print(f"雪球集成测试失败: {e}")


def main():
    """主测试函数"""
    print("🚀 开始股票数据集成测试")
    print()
    
    try:
        # 1. 测试工厂初始化
        test_factory_initialization()
        print()
        
        # 2. 测试AKShare A股数据
        test_akshare_a_share()
        print()
        
        # 3. 测试自动提供者选择
        test_automatic_provider_selection()
        print()
        
        # 4. 测试股票搜索
        test_stock_search()
        print()
        
        # 5. 测试提供者降级
        test_provider_fallback()
        print()
        
        # 6. 测试多市场支持
        test_multiple_markets()
        print()
        
        # 7. 测试雪球集成
        asyncio.run(test_xueqiu_integration())
        print()
        
        print("✅ 股票数据集成测试完成")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 