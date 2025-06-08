from core.enum.indicator_group import IndicatorGroup
from core.indicator.base_indicator import BaseIndicator
from core.utils.utils import UtilsHelper


class VolumeSuperTrendAIIndicator(BaseIndicator):
    # super_trend参数
    len = 10
    factor = 3.0
    maSrc = "WMA"

    # KNN参数
    k = 3
    n = 10
    KNN_PriceLen = 20
    KNN_STLen = 100

    def __init__(
        self, len=10, factor=3.0, maSrc="WMA", k=3, n=10, KNN_PriceLen=20, KNN_STLen=100
    ):
        self.len = len
        self.factor = factor
        self.maSrc = maSrc
        self.k = k
        self.n = max(k, n)  # 确保n至少为k
        self.KNN_PriceLen = KNN_PriceLen
        self.KNN_STLen = KNN_STLen

    def get_key(self):
        return f"Volumesuper_trendAI({self.len},{self.factor},{self.maSrc},{self.k},{self.n})_indicator"

    def get_group(self):
        return IndicatorGroup.POWER

    def calculate(self, kl_data: list):
        length = len(kl_data)
        if length < max(self.len, self.KNN_PriceLen, self.KNN_STLen) + self.n:
            # 数据不足
            return {"posData": [0] * length, "score": 0}

        # 提取数据
        close_data = []
        volume_data = []
        highData = []
        lowData = []
        for klItem in kl_data:
            close_data.append(klItem.close)
            volume_data.append(klItem.volume)
            highData.append(klItem.high)
            lowData.append(klItem.low)

        # 计算super_trend
        posData = []
        super_trend, direction = self._calculate_super_trend(
            close_data, highData, lowData, volume_data
        )

        # 计算KNN参数
        price = self._calculate_wma(close_data, self.KNN_PriceLen)
        st = self._calculate_wma(super_trend, self.KNN_STLen)

        # 收集数据点及其对应标签
        data = super_trend[-self.n :]
        labels = []
        for i in range(self.n):
            idx = length - self.n + i
            label = 1 if price[idx] > st[idx] else 0
            labels.append(label)

        # 对当前点进行分类
        current_super_trend = super_trend[-1]
        label = self._knn_weighted(data, labels, self.k, current_super_trend)

        # 计算趋势信号
        for i in range(length):
            if i < 1:
                posData.append(0)
                continue

            if i < length - self.n:
                # 对于历史数据，仅使用super_trend方向
                posData.append(direction[i])
            else:
                # 对于最新的n个数据点，根据KNN结果调整方向
                idx = i - (length - self.n)
                if label == 1 and direction[i] == -1:
                    posData.append(1)  # 上涨趋势
                elif label == 0 and direction[i] == 1:
                    posData.append(-1)  # 下跌趋势
                else:
                    posData.append(direction[i])

        return {"posData": posData, "score": super_trend[-1]}

    def _calculate_super_trend(self, close_data, highData, lowData, volume_data):
        length = len(close_data)
        utils = UtilsHelper()

        # 计算加权移动平均价格
        vol_price = []
        for i in range(length):
            vol_price.append(close_data[i] * volume_data[i])

        if self.maSrc == "SMA":
            vwma = [
                utils.sma(vol_price, self.len)[i] / utils.sma(volume_data, self.len)[i]
                if utils.sma(volume_data, self.len)[i] > 0
                else close_data[i]
                for i in range(length)
            ]
        elif self.maSrc == "EMA":
            vwma = [
                utils.ema(vol_price, self.len)[i] / utils.ema(volume_data, self.len)[i]
                if utils.ema(volume_data, self.len)[i] > 0
                else close_data[i]
                for i in range(length)
            ]
        elif self.maSrc == "WMA":
            vwma = [
                utils.wma(vol_price, self.len)[i] / utils.wma(volume_data, self.len)[i]
                if utils.wma(volume_data, self.len)[i] > 0
                else close_data[i]
                for i in range(length)
            ]
        elif self.maSrc == "RMA":
            vwma = [
                utils.rma(vol_price, self.len)[i] / utils.rma(volume_data, self.len)[i]
                if utils.rma(volume_data, self.len)[i] > 0
                else close_data[i]
                for i in range(length)
            ]
        else:  # VWMA
            vwma = utils.wma(vol_price, self.len)

        # 计算ATR
        tr_data = []
        for i in range(length):
            if i == 0:
                tr_data.append(highData[i] - lowData[i])
            else:
                tr = max(
                    highData[i] - lowData[i],
                    abs(close_data[i - 1] - highData[i]),
                    abs(close_data[i - 1] - lowData[i]),
                )
                tr_data.append(tr)

        atr = utils.rma(tr_data, self.len)

        # 计算上下轨
        upper_band = [0] * length
        lower_band = [0] * length

        for i in range(length):
            upper_band[i] = vwma[i] + self.factor * atr[i]
            lower_band[i] = vwma[i] - self.factor * atr[i]

        # 计算super_trend
        super_trend = [0] * length
        direction = [0] * length

        for i in range(1, length):
            lower_band[i] = (
                lower_band[i]
                if lower_band[i] > lower_band[i - 1]
                or close_data[i - 1] < lower_band[i - 1]
                else lower_band[i - 1]
            )
            upper_band[i] = (
                upper_band[i]
                if upper_band[i] < upper_band[i - 1]
                or close_data[i - 1] > upper_band[i - 1]
                else upper_band[i - 1]
            )
            if super_trend[i - 1] == upper_band[i - 1]:
                direction[i] = 1 if close_data[i] > upper_band[i] else -1
            else:
                direction[i] = -1 if close_data[i] < lower_band[i] else 1
            super_trend[i] = lower_band[i] if direction[i] == 1 else upper_band[i]

        return super_trend, direction

    def _calculate_wma(self, data, dayCount):
        utils = UtilsHelper()
        return utils.wma(data, dayCount)

    def _distance(self, x1, x2):
        return abs(x1 - x2)

    def _knn_weighted(self, data, labels, k, x):
        n = len(data)
        distances = []
        indices = list(range(n))

        # 计算与所有点的距离
        for i in range(n):
            dist = self._distance(x, data[i])
            distances.append(dist)

        # 排序距离及对应索引
        for i in range(n - 1):
            for j in range(n - i - 1):
                if distances[j] > distances[j + 1]:
                    distances[j], distances[j + 1] = distances[j + 1], distances[j]
                    indices[j], indices[j + 1] = indices[j + 1], indices[j]

        # 计算k个近邻的加权和
        weighted_sum = 0.0
        total_weight = 0.0

        for i in range(k):
            index = indices[i]
            weight = 1.0 / (distances[i] + 0.000001)  # 防止除零
            weighted_sum += weight * labels[index]
            total_weight += weight

        return 1 if weighted_sum / total_weight > 0.5 else 0
