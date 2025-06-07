from typing import Optional

from core.models.ticker import Ticker
from core.models.ticker_score import TickerScore
from core.schema.k_line import KLine

from .normal_score import NormalScore
from .trend_score import TrendScore


class Score:
    rule = TrendScore()

    def __init__(self, rule: Optional[list] = None):
        """
        初始化评分规则
        """
        if rule is not None:
            self.rule = rule
        else:
            self.rule = TrendScore()

    def calculate(
        self,
        ticker: Ticker,
        kl_data: list[KLine],
        strategyData: Optional[list] = None,
        indicatorData: Optional[list] = None,
        valuationData: Optional[list] = None,
    ) -> list[TickerScore]:
        """
        计算评分
        """
        return self.rule.calculate(
            ticker, kl_data, strategyData, indicatorData, valuationData
        )
