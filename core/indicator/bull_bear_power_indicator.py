from typing import Any

from core.enum.indicator_group import IndicatorGroup
from core.indicator.base_indicator import BaseIndicator
from core.schema.k_line import KLine
from core.utils.utils import UtilsHelper


class BullBearPowerIndicator(BaseIndicator):
    day_count = 50
    atr_day = 5

    def get_key(self) -> str:
        return "BUll_BEAR_POWER_indicator"

    def get_group(self) -> IndicatorGroup:
        return IndicatorGroup.POWER

    def calculate(self, kl_data: list[KLine]):
        """
        计算指标
        """
        length = len(kl_data)
        close_data = []
        high_data = []
        low_data = []
        pos_data = []
        for kl_item in kl_data:
            high_data.append(kl_item.high)
            low_data.append(kl_item.low)
            close_data.append(kl_item.close)

        atr_data = UtilsHelper().ratr(kl_data, self.atr_day)
        lowest_data = UtilsHelper().lowest(low_data, self.day_count)
        highest_data = UtilsHelper().highest(high_data, self.day_count)

        score = 0
        for i in range(length):
            bull_trend = (
                (close_data[i] - lowest_data[i]) / atr_data[i] if atr_data[i] > 0 else 0
            )
            bear_trend = (
                (highest_data[i] - close_data[i]) / atr_data[i] if atr_data[i] > 0 else 0
            )
            score = bull_trend - bear_trend
            pos_data.append(1 if score > 0 else (-1 if score < 0 else 0))
        return {"posData": pos_data, "score": score}
