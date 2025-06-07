import pandas as pd

from core.enum.indicator_group import IndicatorGroup
from core.indicator.base_indicator import BaseIndicator
from core.utils.utils import UtilsHelper


class RSIIndicator(BaseIndicator):
    day_count = 14

    def get_key(self):
        return "RSI_indicator"

    def get_group(self):
        return IndicatorGroup.POWER

    def calculate(self, kl_data):
        length = len(kl_data)
        pos_data = []
        up_temp = []
        down_temp = []
        rsi_data = []
        k_line = pd.DataFrame(kl_data)

        for i in range(length):
            if i < 1:
                up_temp.append(0)
                down_temp.append(0)
                continue
            close = k_line["close"][i]
            last_close = k_line["close"][i - 1]
            up_temp.append(max(close - last_close, 0))
            down_temp.append(abs(close - last_close))

        ma_up = UtilsHelper().ma(up_temp, self.day_count, 1)
        ma_down = UtilsHelper().ma(down_temp, self.day_count, 1)
        for i in range(length):
            if i < 1:
                pos_data.append(0)
                rsi_data.append(0)
                continue
            rsi = (ma_up[i] / ma_down[i]) * 100 if ma_down[i] > 0 else 100
            rsi_data.append(rsi)
            if rsi > 80:
                pos_data.append(-1)
            elif rsi > 50:
                pos_data.append(1)
            elif rsi > 20:
                pos_data.append(-1)
            else:
                pos_data.append(1)

        return {"posData": pos_data, "score": rsi_data[length - 1]}
