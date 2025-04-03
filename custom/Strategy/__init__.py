from core.strategy.art_dl_strategy import ARTDLStrategy
from core.strategy.ma_base_strategy import MABaseStrategy
from core.strategy.cci_ma_strategy import CCIMaStrategy
from core.strategy.cci_wma_strategy import CCIWmaStrategy
from core.strategy.boll_dl_strategy import BollDLStrategy

from core.utils import UtilsHelper
import math

strategy = [
    BollDLStrategy(),
    CCIWmaStrategy(),
    CCIMaStrategy(),
    ARTDLStrategy(),
    MABaseStrategy()
]
    
            