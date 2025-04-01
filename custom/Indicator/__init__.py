from core.Indicator.SMAIndicator import SMAIndicator
from core.Indicator.EMAIndicator import EMAIndicator
from core.Indicator.CCIIndicator import CCIIndicator
from core.Indicator.MACDIndicator import MACDIndicator
from core.Indicator.KDJIndicator import KDJIndicator
from core.Indicator.RSIIndicator import RSIIndicator
from core.Indicator.WMSRIndicator import WMSRIndicator
from core.Indicator.BullBearPowerIndicator import BullBearPowerIndicator

indicators = [
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
    MACDIndicator(12,26,9),
    KDJIndicator(),
    RSIIndicator(),
    WMSRIndicator(14),
    BullBearPowerIndicator()
]
    