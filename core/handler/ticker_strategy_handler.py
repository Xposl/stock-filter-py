import math
from typing import Optional

from core.enum.ticker_k_type import TickerKType
from core.models.ticker import Ticker
from core.models.ticker_strategy import TickerStrategy
from core.schema.k_line import KLine
from core.service.ticker_strategy_repository import TickerStrategyRepository
from core.strategy import DEFAULT_STRATEGIES
from core.strategy.base_strategy import BaseStrategy
from core.utils.utils import UtilsHelper


class StrategyCalculator:
    """策略组合管理类"""

    def __init__(self, group: Optional[list[BaseStrategy]] = None):
        """初始化策略组合

        Args:
            group: 策略组列表，默认使用 DEFAULT_STRATEGIES
        """
        self.group = group if group is not None else DEFAULT_STRATEGIES
        self.group_map = {}
        self.profit_init = 100000

        for item in self.group:
            self.group_map[item.get_key()] = item

    def calculate(self, kl_data: list[KLine]):
        """计算所有策略结果

        Args:
            kl_data: K线数据列表

        Returns:
            dict: 策略计算结果字典
        """
        result = {}
        for item in self.group:
            res = self.calculate_by_key(item.get_key(), kl_data)
            result[item.get_key()] = res
        return result

    def calculate_by_key(self, strategy_key: str, kl_data: list[KLine]):
        """根据策略键名计算策略结果

        Args:
            strategy_key: 策略键名
            kl_data: K线数据列表

        Returns:
            dict: 策略计算结果
        """
        if self.group_map[strategy_key] is None:
            raise Exception("error，找不到策略", strategy_key)
        return self.calculate_strategy(self.group_map[strategy_key], kl_data)

    def calculate_strategy(self, strategy_obj: TickerStrategy, kl_data: list[KLine]):
        """计算单个策略的交易结果

        Args:
            strategy_obj: 策略对象
            kl_data: K线数据列表

        Returns:
            dict: 策略交易结果
        """
        result = {
            "net_profit": 0,  # 利润
            "net_profit_pre": 0,  # 利润率
            "gross_profit": 0,  # 毛利润
            "gross_profit_pre": 0,  # 毛利润率
            "gross_loss": 0,  # 毛损失
            "gross_loss_pre": 0,  # 毛损失率
            "hold_return": 0,  # 买入到今利润
            "hold_return_pre": 0,  # 买入到今利润率
            "trades": 0,  # 交易笔数
            "win_trades": 0,  # 挣钱交易
            "loss_trades": 0,  # 亏损交易
            "keep_days": 0,  # 平均持仓时间
            "win_keep_days": 0,  # 盈利平均持仓时间
            "loss_keep_days": 0,  # 亏损平均持仓时间
            "profitable": 0,  # 胜率
            "avg_win_pre": 0,  # 平均盈利率
            "avg_loss_pre": 0,  # 平均亏损率
            "ratio": 0,  # 盈亏比
            "status": 0,  # 当前状态-1:做空 1:做多
            "days": 0,  # 当前状态持续时间
            "profit": 0,  # 当前状态利润
        }
        length = len(kl_data)
        status = 0  # 当前交易状态
        unit = 1  # 交易股份数量
        profit = 0  # 当前浮盈
        ini_price = None  # 第一次买入价格
        start_price = None  # 本次交易买入价格
        start_time = None  # 本次交易买入时机
        start_k_index = 0  # 本次交易开始的K线
        close = 0  # 最后交易日的价格

        pos_data = strategy_obj.calculate(kl_data)
        if len(pos_data) != length:
            raise Exception("策略数据错误,数据长度不符", length, len(pos_data))

        trade_data = []
        for i in range(length):
            open_price = kl_data[i].open
            close = kl_data[i].close

            # 出现信号第二天，进行操作
            if result["days"] == 1 and status == 1:
                unit = UtilsHelper().calcu_integer(self.profit_init, abs(open_price))
                if unit > 0:  # 判断资金是否足够买入
                    # 做多,以开盘价进行操作
                    if ini_price is None:
                        ini_price = open_price
                    start_price = open_price
                    start_k_index = i
                    start_time = kl_data[i].time_key
                    profit = 0

            elif result["days"] == 1 and status == -1:
                # 清仓
                if start_price is not None and start_k_index is not None:
                    # 浮动利率
                    profit = (open_price - start_price) * unit
                    keep_days = i - start_k_index + 1
                    start_k_index = None
                    if profit >= 0:
                        result["win_trades"] = result["win_trades"] + 1
                        result["gross_profit"] = result["gross_profit"] + profit
                        result["win_keep_days"] = keep_days
                    else:
                        result["gross_loss"] = result["gross_loss"] - profit
                        result["loss_trades"] = result["loss_trades"] + 1
                        result["loss_keep_days"] = keep_days

                    trade_data.append(
                        {
                            "start_date": start_time.strftime("%Y-%m-%d %H:%M:%S")
                            if hasattr(start_time, "strftime")
                            else start_time,
                            "end_date": kl_data[i].time_key.strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                            if hasattr(kl_data[i].time_key, "strftime")
                            else kl_data[i].time_key,
                            "buy": start_price,
                            "unit": unit,
                            "sell": open_price,
                            "keep_days": keep_days,
                            "profit": profit,
                            "percent": UtilsHelper().calcu_percent(
                                (open_price - start_price), abs(start_price)
                            ),
                        }
                    )

                # 记录做空时的状态
                start_price = open_price
                start_time = kl_data[i].time_key
                profit = 0
                unit = UtilsHelper().calcu_integer(self.profit_init, abs(start_price))

            # 如果交易状态发生变更，表示出现买卖点
            if pos_data[i] != status:
                result["days"] = 1
                status = pos_data[i]
                # 如果是最后一个交易日，清空当前交易状态
                if i == length - 1 and start_price is not None:
                    profit = 0
            else:
                result["days"] += 1
                # 如果是最后一个交易日，计算浮动盈亏
                if i == length - 1 and start_price is not None:
                    profit = (close - start_price) * unit
                    result["days"] = result["days"] - 1

        # 计算统计数据
        result["keep_days"] = result["win_keep_days"] + result["loss_keep_days"]
        result["trades"] = result["win_trades"] + result["loss_trades"]
        result["gross_profit"] = round(result["gross_profit"], 2)
        result["gross_loss"] = round(result["gross_loss"], 2)
        result["net_profit"] = round(result["gross_profit"] - result["gross_loss"], 2)
        result["net_profit_pre"] = round(
            result["net_profit"] / self.profit_init * 100, 2
        )
        result["gross_profit_pre"] = round(
            result["gross_profit"] / self.profit_init * 100, 2
        )
        result["gross_loss_pre"] = round(
            result["gross_loss"] / self.profit_init * 100, 2
        )

        if ini_price is not None:
            unit = (
                math.floor(self.profit_init / ini_price)
                if ini_price > 0
                else self.profit_init
            )
            result["hold_return"] = (close - ini_price) * unit
            result["hold_return_pre"] = round(
                result["hold_return"] / self.profit_init * 100, 2
            )

        result["avg_win_pre"] = (
            UtilsHelper().calcu_percent(
                result["gross_profit_pre"], result["win_trades"]
            )
            / 100
        )
        result["avg_loss_pre"] = (
            UtilsHelper().calcu_percent(result["gross_loss_pre"], result["loss_trades"])
            / 100
        )
        result["profitable"] = UtilsHelper().calcu_percent(
            result["win_trades"], result["trades"]
        )
        result["ratio"] = UtilsHelper().calcu_percent(
            result["avg_win_pre"], result["avg_loss_pre"]
        )

        result["data"] = trade_data
        result["pos_data"] = pos_data
        result["profit"] = round(profit, 2)
        result["status"] = status
        return result


class TickerStrategyHandler:
    updateTime = ""
    strategies = None

    def __init__(self, strategies: Optional[list] = None):
        """
        初始化
        """
        self.strategies = strategies if strategies is not None else DEFAULT_STRATEGIES

    def calculate(self, kl_data: list[KLine]):
        """
        计算策略
        """
        return StrategyCalculator(self.strategies).calculate(kl_data)

    def update_ticker_strategy(
        self, ticker: Ticker, kl_data: list[KLine], updateTime: str = None
    ):
        """
        更新策略
        """
        print("更新策略", ticker.code)
        length = len(kl_data)
        if length == 0:
            print("无数据")
            return

        strategiesResult = self.calculate(kl_data)
        for strategyKey in strategiesResult:
            result = strategiesResult[strategyKey]
            TickerStrategyRepository().update_item(
                ticker.id, strategyKey, TickerKType.DAY.value, updateTime, result
            )
        return strategiesResult
