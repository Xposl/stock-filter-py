from core.enum.indicator_group import IndicatorGroup
from core.indicator.base_indicator import BaseIndicator
from core.utils.utils import UtilsHelper


class CCIIndicator(BaseIndicator):
    day_count = 0

    def __init__(self, day_count):
        self.day_count = day_count

    def get_key(self):
        return "CCI" + str(self.day_count) + "_indicator"

    def get_group(self):
        return IndicatorGroup.POWER

    def calculate(self, kl_data):
        length = len(kl_data)
        pos_data = []

        cci = UtilsHelper().cci(kl_data, self.day_count)

        for i in range(length):
            if i < 2:
                pos_data.append(0)
                continue
            status = 0
            if (
                (cci[i - 1] < -100 and cci[i] >= -100)
                or (cci[i - 1] < 0 and cci[i] >= 0)
                or (cci[i - 1] < 100 and cci[i] >= 100)
            ):
                status = 1
            elif (
                (cci[i - 1] > -100 and cci[i] <= -100)
                or (cci[i - 1] > 0 and cci[i] <= 0)
                or (cci[i - 1] > 100 and cci[i] <= 100)
            ):
                status = -1
            else:
                status = pos_data[i - 1]
            pos_data.append(status)

        return {"posData": pos_data, "score": cci[length - 1]}
