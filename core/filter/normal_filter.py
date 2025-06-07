import pandas as pd

from core.enum.ticker_type import TickerType
from core.service.ticker_score_repository import TickerScoreRepository

from ..utils.utils import UtilsHelper


class NormalFilter:
    def calculate(
        self, ticker, kLineData, strategyData, indicatorData, KScoreData, valuationData
    ):
        if ticker["type"] != TickerType.STOCK.value:
            return False

        length = len(kLineData)
        weekKLineData = UtilsHelper().get_week_line(kLineData)
        kLine = pd.DataFrame(kLineData)
        weekKLine = pd.DataFrame(weekKLineData)

        if length == 0:
            return False

        weekLength = len(weekKLineData)

        len7 = 7 if length > 7 else length
        len13 = 13 if length > 13 else length
        len21 = 21 if length > 21 else length
        len144 = 144 if length > 144 else length
        len169 = 169 if length > 169 else length

        # 7天交易额均线
        maTurnover = UtilsHelper().sma(kLine["turnover"].values, len13)
        nt = 0
        for i in range(length):
            if length - i - 2 < 0:
                break
            if kLine["close"][length - i - 1] < kLine["close"][length - i - 2]:
                nt += 1
            else:
                break
        if maTurnover[length - 1] < 10 * 1000 * 1000 and nt < 4:
            return False

        KScoreData = TickerScoreRepository().get_items_by_ticker_id(ticker["id"])
        kScore = pd.DataFrame(KScoreData)
        maS = UtilsHelper().wma(kScore["score"].values, len7)
        maM = UtilsHelper().wma(kScore["score"].values, len13)
        maL = UtilsHelper().wma(kScore["score"].values, len21)

        weekMa = UtilsHelper().ema(weekKLine["close"].values, len13)
        UtilsHelper().ema(kLine["close"].values, len13)
        UtilsHelper().ema(kLine["close"].values, len144)

        lastIndex = length - 1
        close = kLine["close"][lastIndex]

        if (
            maS[lastIndex] >= maM[lastIndex]
            and maM[lastIndex] > maL[lastIndex]
            and kScore["score"][lastIndex] > 60
        ) or maS[lastIndex] > 60:
            if (
                close > kLine["close"][length - len144]
                and close > kLine["close"][length - len169]
                and close > kLine["close"][length - len21]
            ):
                if abs(close - weekMa[weekLength - 1]) / weekMa[weekLength - 1] < 0.1:
                    return True
        return False
