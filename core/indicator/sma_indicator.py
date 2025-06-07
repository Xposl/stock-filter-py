from core.enum.indicator_group import IndicatorGroup
from core.indicator.base_indicator import BaseIndicator
from core.utils.utils import UtilsHelper


class SMAIndicator(BaseIndicator):
    day_count = 0

    def __init__(self, day_count):
        self.day_count = day_count

    def get_key(self):
        return "SMA" + str(self.day_count) + "_indicator"

    def get_group(self):
        return IndicatorGroup.POWER

    def calculate(self, kl_data):
        length = len(kl_data)
        close_data = []
        pos_data = []
        for kl_item in kl_data:
            close_data.append(kl_item.close)

        ma = UtilsHelper().sma(close_data, self.day_count)
        for i in range(length):
            if i < 2:
                pos_data.append(0)
                continue
            close = close_data[i]
            pos_data.append(1 if close > ma[i] else (-1 if close < ma[i] else 0))

        return {"posData": pos_data, "score": ma[length - 1]}
