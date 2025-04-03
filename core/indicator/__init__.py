from .sma_indicator import SMAIndicator
from .ema_indicator import EMAIndicator
from .cci_indicator import CCIIndicator
from .macd_indicator import MACDIndicator
from .kdj_indicator import KDJIndicator
from .rsi_indicator import RSIIndicator
from .wmsr_indicator import WMSRIndicator
from .bull_bear_power_indicator import BullBearPowerIndicator

defaultIndicators = [
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
    MACDIndicator(13,34,9),
    KDJIndicator(),
    RSIIndicator(),
    WMSRIndicator(14),
    BullBearPowerIndicator()
]

class Indicator:
    group = []
    groupMap = {}

    def __init__(self,group=None):
        if group is not None:
            self.group = group
        else:
            self.group = defaultIndicators
        for item in self.group:
            self.groupMap[item.getKey()] = item

    def getGroupByKey(self,key):
        item = self.groupMap[key]
        return item.getGroup().value if item.getGroup() is not None else 2

    def calculate(self,klData):
        result = {}
        for item in self.group:
            res = self.calculateByKey(item.getKey(),klData)
            result[item.getKey()] = res
        return result


    def calculateByKey(self,indicatorKey, klData):
        if self.groupMap[indicatorKey] is None:
            raise Exception('error，找不到指标',indicatorKey)
        result = {
            'score': 0, #当前数值
            'status':0, #当前状态-1:做空 1:做多
            'days':0, #当前状态持续时间
        }
        length = len(klData)
        data = self.groupMap[indicatorKey].calculate(klData)
        result['score'] = data['score']
        posData = data['posData']

        if len(posData) != length:
            raise Exception('指标数据错误,数据长度不符',length,len(posData))

        result['status'] = posData[length-1]
        result['days'] = 0
        result['history'] = posData
        for i in range(length):
            if(posData[length - i - 1] != result['status']):
                break
            result['days'] += 1
        return result
            