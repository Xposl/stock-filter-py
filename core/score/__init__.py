from typing import Optional

from core.models.ticker import Ticker
from .normal_score import NormalScore
from .trend_score import TrendScore

class Score:
    rule = TrendScore()

    def __init__(self,rule: Optional[list]=None):
        """
        初始化评分规则
        """
        if rule is not None:
            self.rule = rule
        else:
            self.rule = TrendScore()

    def calculate(self,ticker: Ticker,kLineData: Optional[list]=None,strategyData: Optional[list]=None,indicatorData: Optional[list]=None,valuationData: Optional[list]=None):
        """
        计算评分
        """
        return self.rule.calculate(ticker,kLineData,strategyData,indicatorData,valuationData)

            