from core.enum.indicator_group import IndicatorGroup
from core.indicator.base_indicator import BaseIndicator
from core.schema.k_line import KLine
from core.utils.utils import UtilsHelper


class MACDIndicator(BaseIndicator):
    dif_count = 12
    day_count = 26
    m = 9

    def __init__(self, dif_count, day_count, m):
        self.dif_count = dif_count
        self.day_count = day_count
        self.m = m

    def get_key(self):
        return "MACD(" + str(self.dif_count) + "," + str(self.day_count) + ")_indicator"

    def get_group(self):
        return IndicatorGroup.POWER

    def calculate(self, kl_data: list[KLine]):
        length = len(kl_data)
        close_data = []
        dif = []
        macd = []
        pos_data = []
        for kl_item in kl_data:
            close_data.append(kl_item.close)

        ema_s = UtilsHelper().ema(close_data, self.dif_count)
        ema_l = UtilsHelper().ema(close_data, self.day_count)

        for i in range(length):
            dif.append(ema_s[i] - ema_l[i])

        ema_dif = UtilsHelper().ema(dif, self.m)

        for i in range(length):
            macd.append((dif[i] - ema_dif[i]) * 2)
            pos_data.append(1 if macd[i] > 0 else (-1 if macd[i] < 0 else 0))

        return {"posData": pos_data, "score": macd[length - 1]}
