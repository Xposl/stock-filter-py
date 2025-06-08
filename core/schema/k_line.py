from dataclasses import dataclass
from typing import TypedDict

import numpy as np


@dataclass
class KLine:
    """K线数据"""

    time_key: str
    high: np.float64
    low: np.float64
    open: np.float64
    close: np.float64
    volume: np.float64
    turnover: np.float64
    turnover_rate: np.float64


class KLineDict(TypedDict):
    """K线数据字典"""

    time_key: str
    high: np.float64
    low: np.float64
    open: np.float64
    close: np.float64
    volume: np.float64
    turnover: np.float64
    turnover_rate: np.float64


# 用于序列化和反序列化的辅助函数
def k_line_to_dict(k_line: KLine) -> KLineDict:
    """
    将KLine模型转换为字典，用于数据库操作

    Args:
        k_line: KLine、KLineCreate或KLineUpdate模型

    Returns:
        字典表示
    """
    result = {}
    if isinstance(k_line, KLine):
        result = {
            "time_key": k_line.time_key,
            "high": k_line.high,
            "low": k_line.low,
            "open": k_line.open,
            "close": k_line.close,
            "volume": k_line.volume,
            "turnover": k_line.turnover,
            "turnover_rate": k_line.turnover_rate,
        }

    return result


def k_line_from_dict(data: KLineDict) -> KLine:
    """
    将字典转换为KLine模型
    """
    return KLine(
        time_key=data["time_key"],
        high=data["high"],
        low=data["low"],
        open=data["open"],
        close=data["close"],
        volume=data["volume"],
        turnover=data["turnover"],
        turnover_rate=data["turnover_rate"],
    )
