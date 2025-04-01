from .NormalFilter import NormalFilter


class Filter:
    rule = NormalFilter()

    def __init__(self,rule=None):
        if rule is not None:
            self.rule = rule
        else:
            self.rule = NormalFilter()

    def calculate(self,ticker,kLineData,strategyData,indicatorData,KScoreData,valuationData):
        return self.rule.calculate(ticker,kLineData,strategyData,indicatorData,KScoreData,valuationData)

            