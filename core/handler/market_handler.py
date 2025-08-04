#!/usr/bin/env python3

"""
市场处理器
"""

from datetime import datetime
import logging
from typing import Any, Optional

from core.models.ticker import Ticker
from core.repository.market_repository import MarketRepository

logger = logging.getLogger(__name__)


class MarketTradingStatus:
    def __init__(self, is_trading_day: bool, market_open: bool, next_update_time: str, timezone: str):
        self.is_trading_day = is_trading_day
        self.market_open = market_open
        self.next_update_time = next_update_time
        self.timezone = timezone

class MarketHandler:
    """市场处理器"""

    def __init__(self):
        """
        初始化市场处理器
        """
        self.repository = MarketRepository()


    def get_market_trading_status(self, ticker: Ticker) -> MarketTradingStatus:
        """
        获取市场交易状态

        Returns: MarketTradingStatus
        """
        try:
            market_code_map = {1: "HK", 2: "ZH", 3: "US"}
            market_code = market_code_map.get(ticker.group_id, "ZH")
            
            # 获取市场信息
            market = self.repository.get_by_code(market_code)
            if not market:
                return MarketTradingStatus(True, False, None, "UTC")

            # 导入必要的包
            import pytz
            from datetime import timedelta
            
            # 获取市场时区的当前时间
            market_tz = pytz.timezone(market.timezone)
            now_in_market = datetime.now(market_tz)
            
            # 检查是否为交易日
            weekday = now_in_market.weekday()
            is_trading_day = market.is_trading_day(weekday)
            
            # 检查是否在交易时间内
            current_time = now_in_market.time()
            market_open = market.open_time <= current_time <= market.close_time
            
            # 计算下次更新时间（市场闭市后30分钟）
            next_update_time = None
            if is_trading_day and market_open:
                # 如果市场开市，设置下次更新时间为当前时间+30分钟
                next_update_time = (datetime.now() + timedelta(minutes=30)).isoformat()
            elif is_trading_day and not market_open:
                # 如果交易日但已闭市，设置下次更新时间为次日开市前
                next_update_time = (datetime.now() + timedelta(days=1)).replace(
                    hour=market.open_time.hour,
                    minute=market.open_time.minute
                ).isoformat()
            else:
                # 非交易日，设置下次更新时间为下个交易日开市前
                days_until_monday = (7 - weekday) % 7
                if days_until_monday == 0:
                    days_until_monday = 7
                next_update_time = (datetime.now() + timedelta(days=days_until_monday)).replace(
                    hour=market.open_time.hour,
                    minute=market.open_time.minute
                ).isoformat()

            return MarketTradingStatus(is_trading_day, market_open, next_update_time, market.timezone)

        except Exception as e:
            print(f"获取市场状态失败: {e}")
            return MarketTradingStatus(True, False, None, "UTC")
        
    def is_market_open_now(self, market_code: str) -> bool:
        """
        检查指定市场当前是否开市

        Args:
            market_code: 市场代码 (HK, ZH, US)

        Returns:
            是否开市
        """
        try:
            # 获取市场信息
            market = self.repository.get_by_code(market_code)
            if not market:
                return False

            # 导入必要的包
            from datetime import datetime

            import pytz

            # 获取市场时区的当前时间
            market_tz = pytz.timezone(market.timezone)
            now_in_market = datetime.now(market_tz)

            # 检查是否为交易日
            weekday = now_in_market.weekday()  # 0=Monday, 6=Sunday
            if not market.is_trading_day(weekday):
                return False

            # 检查是否在交易时间内
            current_time = now_in_market.time()
            return market.open_time <= current_time <= market.close_time

        except Exception as e:
            print(f"检查市场开市状态失败: {e}")
            return False