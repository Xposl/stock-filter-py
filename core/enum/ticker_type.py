from enum import Enum


class TickerType(Enum):
    DEL = 0  # 无效
    STOCK = 1  # 正股
    IDX = 2  # 指数
    BOND = 3  # 债券
    DRVT = 4  # 期权
    FUTURE = 5  # 期货
    ETF = 11  # 信托,基金
    BWRT = 50  # 一揽子权证
    WARRANT = 60  # 窝轮
    PLATE = 90  # 板块
    PLATESET = 91  # 板块集
