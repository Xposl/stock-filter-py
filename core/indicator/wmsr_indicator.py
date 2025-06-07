import pandas as pd

from core.enum.indicator_group import IndicatorGroup
from core.indicator.base_indicator import BaseIndicator
from core.utils.utils import UtilsHelper


class WMSRIndicator(BaseIndicator):
    day_count = 14

    def __init__(self, day_count):
        self.day_count = day_count

    def get_key(self):
        return "WMSR" + str(self.day_count) + "_indicator"

    def get_group(self):
        return IndicatorGroup.POWER

    def calculate(self, kl_data):
        length = len(kl_data)
        pos_data = []
        data = []
        k_line = pd.DataFrame(kl_data)
        lowest_data = UtilsHelper().lowest(k_line["low"].values, self.day_count)
        highest_data = UtilsHelper().highest(k_line["high"].values, self.day_count)

        for i in range(length):
            temp1 = highest_data[i] - k_line["close"][i]
            temp2 = highest_data[i] - lowest_data[i]
            wr = -100 * temp1 / temp2 if temp2 > 0 else -100
            data.append(wr)
            status = 0
            if wr > -50:
                status = 1
            elif wr < -50:
                status = -1
            pos_data.append(status)

        return {"posData": pos_data, "score": data[length - 1]}
