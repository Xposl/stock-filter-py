"""
策略模块初始化
"""
from .art_dl_strategy import ArtDLStrategy
from .ma_base_strategy import MaBaseStrategy
from .cci_ma_strategy import CCIMaStrategy
from .cci_wma_strategy import CCIWmaStrategy
from .boll_dl_strategy import BollDLStrategy
from .cci_macd_strategy import CCIMacdStrategy
from .volume_supertrend_ai_strategy import VolumeSuperTrendAIStrategy

DEFAULT_STRATEGIES = [
    BollDLStrategy(),
    CCIWmaStrategy(),
    CCIMaStrategy(),
    ArtDLStrategy(),
    MaBaseStrategy(),
    CCIMacdStrategy(),
    VolumeSuperTrendAIStrategy()
]
