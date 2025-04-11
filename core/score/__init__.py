from .normal_score import NormalScore
from .trend_score import TrendScore

class Score:
    rule = TrendScore()

    def __init__(self,rule=None):
        if rule is not None:
            self.rule = rule
        else:
            self.rule = TrendScore()

    def calculate(self,ticker,kLineData,strategyData,indicatorData,valuationData):
        return self.rule.calculate(ticker,kLineData,strategyData,indicatorData,valuationData)

            