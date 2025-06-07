
from core.enum.indicator_group import IndicatorGroup
from core.indicator.base_indicator import BaseIndicator
from core.schema.k_line import KLine
from core.utils.utils import UtilsHelper


class KDJIndicator(BaseIndicator):
    P1 = 9
    P2 = 3
    P3 = 3

    def get_key(self):
        return "KDJ_indicator"

    def get_group(self):
        return IndicatorGroup.POWER

    def calculate(self, kl_data: list[KLine]):
        length = len(kl_data)
        close_data = []
        high_data = []
        low_data = []
        rsv_data = []
        j_data = []
        pos_data = []
        for kl_item in kl_data:
            high_data.append(kl_item.high)
            low_data.append(kl_item.low)
            close_data.append(kl_item.close)

        lowest_data = UtilsHelper().lowest(low_data, self.P1)
        highest_data = UtilsHelper().highest(high_data, self.P1)

        for i in range(length):
            divid = highest_data[i] - lowest_data[i]
            rsv = (close_data[i] - lowest_data[i]) / divid if divid > 0 else 0
            rsv = rsv * 100
            rsv_data.append(rsv)

        k_data = UtilsHelper().ma(rsv_data, self.P2, 1)
        d_data = UtilsHelper().ma(k_data, self.P3, 1)

        for i in range(length):
            j_value = 3 * k_data[i] - 2 * d_data[i]
            j_data.append(j_value)

            if i < 2:
                pos_data.append(0)
                continue

            if j_value > 100 and k_data[i] > 90 and d_data[i] > 80:
                pos_data.append(-1)
            elif j_value < 0 and k_data[i] < 10 and d_data[i] < 20:
                pos_data.append(1)
            elif j_value > k_data[i]:
                pos_data.append(1)
            elif j_value < k_data[i]:
                pos_data.append(-1)
            else:
                pos_data.append(0)

        return {"posData": pos_data, "score": j_data[length - 1]}
