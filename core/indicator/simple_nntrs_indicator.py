import statistics

import pandas as pd

from core.enum.indicator_group import IndicatorGroup
from core.indicator.base_indicator import BaseIndicator
from core.schema.k_line import KLine
from core.utils.utils import UtilsHelper


class SimpleNNTRSIIndicator(BaseIndicator):
    """简单神经网络转换RSI指标 (Simple Neural Network Transformed RSI)

    基于QuantraAI的'Simple Neural Network Transformed RSI'指标
    这个指标将RSI通过简单的神经网络处理进行平滑，并添加标准差带
    同时实现了TradingView和ThinkorSwim两个平台版本的核心算法
    """

    def __init__(
        self, rsi_length=14, nn_length=5, sd_lookback=365, sd_mult=2.0, use_median=False
    ):
        """初始化SimpleNNTRSIIndicator

        Args:
            rsi_length: RSI计算周期，默认14
            nn_length: 神经网络平滑长度，默认5
            sd_lookback: 标准差回顾周期，默认365（与原始代码保持一致）
            sd_mult: 标准差倍数，用于确定超买超卖区间，默认2.0
            use_median: 是否使用中值线而非固定的50中线，默认False
        """
        self.rsi_length = rsi_length
        self.nn_length = nn_length
        self.sd_lookback = sd_lookback
        self.sd_mult = sd_mult
        self.use_median = use_median
        self.utils = UtilsHelper()

    def get_key(self):
        """获取指标的唯一键名"""
        return "SimpleNNTRSI_indicator"

    def get_group(self):
        """获取指标所属的组"""
        return IndicatorGroup.POWER

    def _calculate_rsi(self, kl_data: list[KLine]):
        """计算RSI

        与原始ThinkorSwim版本一致，使用标准RSI计算方法

        Args:
            kl_data: K线数据

        Returns:
            RSI数值列表
        """
        length = len(kl_data)
        up_temp = []
        down_temp = []
        rsi_data = []
        k_line = pd.DataFrame(kl_data)

        # 计算上涨和下跌值
        for i in range(length):
            if i < 1:
                up_temp.append(0)
                down_temp.append(0)
                continue
            close = k_line["close"][i]
            last_close = k_line["close"][i - 1]
            up_temp.append(max(close - last_close, 0))
            down_temp.append(abs(min(close - last_close, 0)))

        # 计算RSI (在TradingView中使用DynamicFunc.Rsi)
        ma_up = self.utils.sma(up_temp, self.rsi_length)
        ma_down = self.utils.sma(down_temp, self.rsi_length)
        for i in range(length):
            if i < 1:
                rsi_data.append(50)  # 初始值设为中性50
                continue
            if ma_down[i] > 0:
                rs = ma_up[i] / ma_down[i]
                rsi = 100 - (100 / (1 + rs))
            else:
                rsi = 100
            rsi_data.append(rsi)

        return rsi_data

    def _apply_nn_smoothing(self, rsi_data):
        """应用简单神经网络平滑

        根据原始ThinkorSwim代码：
        def nnOutput = Sum(rsi1 * 1 / nnLength, nnLength);

        这是一个简单的滑动窗口求和，每个值乘以相同的权重(1/nnLength)

        Args:
            rsi_data: RSI数据列表

        Returns:
            平滑后的数据列表
        """
        length = len(rsi_data)
        nn_output = []

        for i in range(length):
            # 计算可用的回溯点数
            lookback = min(i + 1, self.nn_length)

            # 如果没有足够的数据点
            if lookback < 1:
                nn_output.append(rsi_data[i])
                continue

            # 计算加权和 (与ThinkorSwim版本一致)
            sum_value = 0.0
            for j in range(lookback):
                # 每个值乘以相同权重
                sum_value += rsi_data[i - j] * (1.0 / self.nn_length)

            nn_output.append(sum_value)

        return nn_output

    def _calculate_median(self, data):
        """计算数据的中值序列

        根据ThinkorSwim版本：def median = Median(nnOutput, MedianLength);

        Args:
            data: 输入数据

        Returns:
            中值序列
        """
        length = len(data)
        result = []

        for i in range(length):
            if i < self.sd_lookback:
                # 使用可用数据计算中值
                window = data[max(0, i - self.sd_lookback + 1) : i + 1]
                if window:
                    result.append(statistics.median(window))
                else:
                    result.append(50)  # 默认值
            else:
                # 使用完整窗口
                window = data[i - self.sd_lookback + 1 : i + 1]
                result.append(statistics.median(window))

        return result

    def _calculate_std_bands(self, data):
        """计算标准差带

        根据ThinkorSwim版本：
        script stdv_bands {
            input _src = close;
            input _length = 365;
            input _mult = 1;
            def basis = Average(_src, _length);
            def dev   = _mult * StDev(_src, _length);
            plot up = basis + dev;
            plot dn = basis - dev;
        }

        Args:
            data: 输入数据列表

        Returns:
            (mean/median, upper1, lower1, upper2, lower2) 均值/中值和标准差区间
        """
        length = len(data)

        # 根据use_median选项决定使用均值或中值作为中心线
        if self.use_median:
            center = self._calculate_median(data)
        else:
            center = self.utils.sma(data, self.sd_lookback)

        # 计算标准差
        std_dev = []
        for i in range(length):
            if i < self.sd_lookback:
                # 使用可用数据点
                lookback = max(1, i)
                total = 0
                for j in range(lookback):
                    total += (data[i - j] - center[i]) ** 2
                std_dev.append((total / lookback) ** 0.5)
            else:
                # 使用完整窗口
                total = 0
                for j in range(self.sd_lookback):
                    total += (data[i - j] - center[i]) ** 2
                std_dev.append((total / self.sd_lookback) ** 0.5)

        # 计算标准差带
        upper1 = []
        lower1 = []
        upper2 = []
        lower2 = []

        for i in range(length):
            # sdMult/2 对应第一个标准差带
            upper1.append(center[i] + std_dev[i] * self.sd_mult / 2)
            lower1.append(center[i] - std_dev[i] * self.sd_mult / 2)
            # sdMult 对应第二个标准差带
            upper2.append(center[i] + std_dev[i] * self.sd_mult)
            lower2.append(center[i] - std_dev[i] * self.sd_mult)

        return center, upper1, lower1, upper2, lower2

    def calculate(self, kl_data):
        """计算指标

        Args:
            kl_data: K线数据

        Returns:
            包含信号和当前分数的字典
        """
        length = len(kl_data)
        if length == 0:
            return {"posData": [], "score": 0}

        # 计算RSI
        rsi_data = self._calculate_rsi(kl_data)

        # 应用神经网络平滑
        nn_output = self._apply_nn_smoothing(rsi_data)

        # 计算标准差带
        center, upper1, lower1, upper2, lower2 = self._calculate_std_bands(nn_output)

        # 生成买卖信号 (对应"Trend Following"模式)
        pos_data = []
        for i in range(length):
            if i < 1:
                pos_data.append(0)  # 第一个数据点没有信号
                continue

            # 趋势跟随信号
            # 根据ThinkorSwim版本：col = if (if NoHA then nnOutput else harc) > cross then
            # 1 else -1
            cross_value = 50 if not self.use_median else center[i]

            if nn_output[i] > cross_value:
                # 当NN-RSI高于中线/中值线时做多
                pos_data.append(1)
            else:
                # 当NN-RSI低于中线/中值线时做空
                pos_data.append(-1)

            # 注: ThinkorSwim版本还支持其他信号模式：
            # - None: 无信号
            # - Candles: 基于Heikin Ashi蜡烛图
            # - Extremities: 当值超过标准差带时
            # - Reversions: 基于反转模式

        return {"posData": pos_data, "score": nn_output[-1]}  # 返回最新的指标值
