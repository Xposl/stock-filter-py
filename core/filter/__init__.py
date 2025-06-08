from .normal_filter import NormalFilter


class Filter:
    rule = NormalFilter()

    def __init__(self, rule=None):
        if rule is not None:
            self.rule = rule
        else:
            self.rule = NormalFilter()

    def calculate(
        self, ticker, k_line_data, strategy_data, indicator_data, k_score_data, valuation_data
    ):
        return self.rule.calculate(
            ticker, k_line_data, strategy_data, indicator_data, k_score_data, valuation_data
        )
