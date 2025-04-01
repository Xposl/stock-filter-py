from enum import Enum

class TickerGroup(Enum):
    HK = 1 #港股
    ZH = 2 #A股
    US = 3 #美股

def getGroupIdByCode(code):
    if code.startswith('HK'):
        return TickerGroup.HK.value
    elif code.startswith('US'):
        return TickerGroup.US.value
    elif code.startswith('SZ') or code.startswith('SH'):
        return TickerGroup.ZH.value