from core.Strategy.ARTDLStrategy import ARTDLStrategy
from core.Strategy.MABaseStrategy import MABaseStrategy
from core.Strategy.CCIMaStrategy import CCIMaStrategy
from core.Strategy.CCIWmaStrategy import CCIWmaStrategy
from core.Strategy.BollDLStrategy import BollDLStrategy

from core.utils import UtilsHelper
import math

strategy = [
    BollDLStrategy(),
    CCIWmaStrategy(),
    CCIMaStrategy(),
    ARTDLStrategy(),
    MABaseStrategy()
]
    
            