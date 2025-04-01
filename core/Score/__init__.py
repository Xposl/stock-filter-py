from .NormalScore import NormalScore


from core.utils import UtilsHelper
import math

class Score:
    rule = NormalScore()

    def __init__(self,rule=None):
        if rule is not None:
            self.rule = rule
        else:
            self.rule = NormalScore()

    def calculate(self,ticker,kLineData,strategyData,indicatorData,valuationData):
        return self.rule.calculate(ticker,kLineData,strategyData,indicatorData,valuationData)

            