

from dataclasses import dataclass
from typing import TypedDict

@dataclass
class KLine:
    """K线数据"""
    time_key: str
    high: float
    low: float
    open: float
    close: float
    volume: float
    turnover: float
    turnover_rate: float

class KLineDict(TypedDict):
    """K线数据字典"""
    time_key: str
    high: float
    low: float
    open: float
    close: float
    volume: float
    turnover: float
    turnover_rate: float

# 用于序列化和反序列化的辅助函数
def K_line_to_dict(kLine: KLine) -> KLineDict:
    """
    将KLine模型转换为字典，用于数据库操作
    
    Args:
        score: KLine、KLineCreate或KLineUpdate模型
    
    Returns:
        字典表示
    """
    result = {}
    if isinstance(kLine, KLine):
        result = {
            'time_key': kLine.time_key,
            'high': kLine.high,
            'low': kLine.low,
            'open': kLine.open,
            'close': kLine.close,
            'volume': kLine.volume,
            'turnover': kLine.turnover,
            'turnover_rate': kLine.turnover_rate,
        }
    
    return result

def K_line_from_dict(data: KLineDict) -> KLine:
    """
    将字典转换为KLine模型
    """
    return KLine(
        time_key=data['time_key'],
        high=data['high'],
        low=data['low'],
        open=data['open'],
        close=data['close'],
        volume=data['volume'],
        turnover=data['turnover'],
        turnover_rate=data['turnover_rate'],
    )

    