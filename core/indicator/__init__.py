from .bull_bear_power_indicator import BullBearPowerIndicator
from .cci_indicator import CCIIndicator
from .ema_indicator import EMAIndicator
from .kdj_indicator import KDJIndicator
from .macd_indicator import MACDIndicator
from .rsi_indicator import RSIIndicator
from .simple_nntrs_indicator import SimpleNNTRSIIndicator
from .sma_indicator import SMAIndicator
from .volume_supertrend_ai_indicator import VolumeSuperTrendAIIndicator
from .wmsr_indicator import WMSRIndicator

default_indicators = [
    SMAIndicator(5),
    SMAIndicator(10),
    SMAIndicator(20),
    SMAIndicator(50),
    SMAIndicator(100),
    SMAIndicator(200),
    EMAIndicator(5),
    EMAIndicator(10),
    EMAIndicator(20),
    EMAIndicator(50),
    EMAIndicator(100),
    EMAIndicator(200),
    CCIIndicator(14),
    MACDIndicator(13, 34, 9),
    KDJIndicator(),
    RSIIndicator(),
    WMSRIndicator(14),
    BullBearPowerIndicator(),
    VolumeSuperTrendAIIndicator(),
    SimpleNNTRSIIndicator(),
]


class Indicator:
    group = []
    group_map = {}

    def __init__(self, group=None):
        if group is not None:
            self.group = group
        else:
            self.group = default_indicators
        for item in self.group:
            self.group_map[item.get_key()] = item

    def get_group_by_key(self, key):
        item = self.groupMap[key]
        return item.getGroup().value if item.getGroup() is not None else 2

    def calculate(self, kl_data):
        result = {}
        for item in self.group:
            res = self.calculate_by_key(item.get_key(), kl_data)
            result[item.get_key()] = res
        return result

    def calculate_by_key(self, indicator_key, kl_data):
        if self.group_map[indicator_key] is None:
            raise Exception("error，找不到指标", indicator_key)
        result = {
            "score": 0,  # 当前数值
            "status": 0,  # 当前状态-1:做空 1:做多
            "days": 0,  # 当前状态持续时间
        }
        length = len(kl_data)
        data = self.group_map[indicator_key].calculate(kl_data)
        result["score"] = data["score"]
        pos_data = data["posData"]

        if len(pos_data) != length:
            raise Exception("指标数据错误,数据长度不符", length, len(pos_data))

        result["status"] = pos_data[length - 1]
        result["days"] = 0
        result["history"] = pos_data
        for i in range(length):
            if pos_data[length - i - 1] != result["status"]:
                break
            result["days"] += 1
        return result
