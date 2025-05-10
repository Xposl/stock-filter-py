import math
import sys
from typing import List

from core.schema.k_line import KLine

class UtilsHelper:
    """
    工具类，提供常用的数学和数据处理方法。
    """

    def run_process(self, index: int, total: int, title: str, message: str) -> None:
        """
        打印进度条。
        """
        print("\r", end="")
        process = int(index / (total - 1) * 100) if total > 1 else 100
        print(f"{title}: {process}%: ", "▋" * (process // 2), message, end="")
        sys.stdout.flush()

    def calcu_percent(self, dividend: float, divisor: float) -> float:
        """
        计算百分比。
        """
        return round(dividend / divisor * 100, 2) if divisor > 0 else 0

    def calcu_integer(self, dividend: float, divisor: float) -> int:
        """
        计算整数商。
        """
        return math.floor(dividend / divisor) if divisor > 0 else 0

    def keep_up_trend(self, data: List[float], sign: float, day: int, length: int) -> bool:
        """
        判断是否持续上涨。
        """
        start = day - length if day - length > 0 else 0
        for i in range(start, day):
            if data[i] < sign:
                return False
        return True

    def double_line_pos(self, price_data: List[float], adjust_base_data: List[float], adjust_data: List[float]) -> List[int]:
        """
        通道交易点计算函数。
        """
        stop_data = []
        pos_data = []
        for i in range(len(price_data)):
            price = price_data[i]
            adjust_base = adjust_base_data[i]
            adjust = adjust_data[i]
            if i == 0:
                stop_data.append(adjust_base - adjust)
                continue
            last_price = price_data[i - 1]
            last_stop_data = stop_data[i - 1]
            v1 = adjust_base - adjust if price > last_stop_data else adjust_base + adjust
            v2 = min(adjust_base + adjust, last_stop_data) if price < last_stop_data and last_price < last_stop_data else v1
            v3 = max(adjust_base - adjust, last_stop_data) if price > last_stop_data and last_price > last_stop_data else v2
            stop_data.append(v3)

        for i in range(len(price_data)):
            if i == 0:
                pos_data.append(0)
                continue
            price = price_data[i]
            last_price = price_data[i - 1]
            last_stop_data = stop_data[i - 1]
            last_pos_data = pos_data[i - 1]
            v1 = -1 if last_price > last_stop_data and price < last_stop_data else last_pos_data
            v2 = 1 if last_price < last_stop_data and price > last_stop_data else v1
            pos_data.append(v2)
        return pos_data

    def keep_down_trend(self, data: List[float], sign: float, day: int, length: int) -> bool:
        """
        判断是否持续下跌。
        """
        start = day - length if day - length > 0 else 0
        for i in range(start, day):
            if data[i] > sign:
                return False
        return True

    def sum_list(self, data: List[float], day_count: int) -> List[float]:
        """
        计算滑动求和。
        """
        result = []
        length = len(data)
        for i in range(length):
            calcu_day = day_count
            if i < day_count - 1:
                calcu_day = i + 1
            s = 0
            for j in range(calcu_day):
                s += data[i - j]
            result.append(s)
        return result

    def avedev(self, data: List[float], day_count: int) -> List[float]:
        """
        平均绝对偏差。
        """
        result = [0]
        length = len(data)
        sma_data = self.sma(data, day_count)
        for i in range(1, length):
            calcu_day = day_count
            if i < day_count - 1:
                calcu_day = i + 1
            s = 0
            for j in range(calcu_day):
                s += abs(data[i - j] - sma_data[i])
            result.append(s / calcu_day)
        return result

    def stddev(self, data: List[float], day_count: int) -> List[float]:
        """
        标准差。
        """
        result = [0]
        length = len(data)
        sma_data = self.sma(data, day_count)
        for i in range(1, length):
            calcu_day = day_count
            if i < day_count - 1:
                calcu_day = i + 1
            s = 0
            for j in range(calcu_day):
                s += (data[i - j] - sma_data[i]) ** 2
            result.append(math.sqrt(s / calcu_day))
        return result

    def highest(self, data: List[float], day_count: int) -> List[float]:
        """
        滑动最高值。
        """
        result = []
        length = len(data)
        for i in range(length):
            calcu_day = day_count
            if i < day_count - 1:
                calcu_day = i + 1
            sub_arr = data[i - calcu_day + 1:i + 1]
            result.append(max(sub_arr))
        return result

    def lowest(self, data: List[float], day_count: int) -> List[float]:
        """
        滑动最低值。
        """
        result = []
        length = len(data)
        for i in range(length):
            calcu_day = day_count
            if i < day_count - 1:
                calcu_day = i + 1
            sub_arr = data[i - calcu_day + 1:i + 1]
            result.append(min(sub_arr))
        return result

    def rma(self, data: List[float], day_count: int) -> List[float]:
        """
        RMA 平滑移动平均。
        """
        result = []
        length = len(data)
        for i in range(length):
            if i == 0:
                result.append(0)
                continue
            alpha = day_count
            res = (data[i] + (alpha - 1) * result[i - 1]) / alpha
            result.append(res)
        return result

    def sma(self, data: List[float], day_count: int) -> List[float]:
        """
        简单移动平均。
        """
        result = [data[0]]
        length = len(data)
        for i in range(1, length):
            calcu_day = day_count
            if i < day_count - 1:
                calcu_day = i + 1
            s = 0
            for j in range(calcu_day):
                s += data[i - j]
            result.append(s / calcu_day)
        return result

    def ema(self, data: List[float], day_count: int) -> List[float]:
        """
        指数移动平均。
        """
        result = [data[0]]
        length = len(data)
        for i in range(1, length):
            calcu_day = day_count
            if i < day_count - 1:
                calcu_day = i + 1
            res = (2 * data[i] + (calcu_day - 1) * result[i - 1]) / (calcu_day + 1)
            result.append(res)
        return result

    def wma(self, data: List[float], day_count: int) -> List[float]:
        """
        加权移动平均。
        """
        result = [data[0]]
        length = len(data)
        for i in range(1, length):
            calcu_day = day_count
            if i < day_count - 1:
                calcu_day = i + 1
            norm = 0
            s = 0
            for j in range(calcu_day):
                weight = (calcu_day - j) * calcu_day
                norm += weight
                s += data[i - j] * weight
            result.append(s / norm)
        return result

    def ma(self, data: List[float], day_count: int, weight: float) -> List[float]:
        """
        一般移动平均。
        """
        result = [data[0]]
        length = len(data)
        for i in range(1, length):
            calcu_day = day_count
            if i < day_count - 1:
                calcu_day = i + 1
            res = (weight * data[i] + (calcu_day - weight) * result[i - 1]) / calcu_day
            result.append(res)
        return result

    def hma(self, data: List[float], day_count: int) -> List[float]:
        """
        Hull 移动平均。
        """
        length = len(data)
        alpha_data = []
        half_day = int(round(day_count / 2, 0))
        sqrt_day = int(round(math.sqrt(day_count), 0))
        half_data = self.wma(data, half_day)
        wma_data = self.wma(data, day_count)
        for i in range(length):
            alpha = 2 * half_data[i] - wma_data[i]
            alpha_data.append(alpha)
        return self.wma(alpha_data, sqrt_day)

    def vwma(self, kl_data: List[KLine], day_count: int) -> List[float]:
        """
        成交量加权移动平均。
        """
        result = []
        data = []
        volume_data = []
        length = len(kl_data)
        for kl_item in kl_data:
            volume_data.append(kl_item.volume)
            data.append(kl_item.close * kl_item.volume)
        ma_data = self.sma(data, day_count)
        ma_volume = self.sma(volume_data, day_count)
        for i in range(length):
            vwma = ma_data[i] / ma_volume[i] if ma_volume[i] > 0 else 0
            result.append(vwma)
        return result

    def tr(self, kl_data: List[KLine]) -> List[float]:
        """
        真实波动幅度（True Range）。
        """
        result = []
        length = len(kl_data)
        for i in range(length):
            day_value = kl_data[i]
            last_day_value = kl_data[i - 1]
            high = day_value.high
            low = day_value.low
            last_close = last_day_value.close
            res = max(max((high - low), abs(last_close - high)), abs(last_close - low))
            result.append(res)
        return result

    def ratr(self, kl_data: List[KLine], day_count: int) -> List[float]:
        """
        计算真实波动幅度均值（RATR）。
        """
        tr_data = self.tr(kl_data)
        return self.rma(tr_data, day_count)

    def typ(self, kl_data: List[KLine]) -> List[float]:
        """
        典型价格。
        """
        result = []
        length = len(kl_data)
        for i in range(length):
            day_value = kl_data[i]
            high = day_value.high
            low = day_value.low
            close = day_value.close
            result.append((high + low + close) / 3)
        return result

    def cci(self, kl_data: List[KLine], day_count: int) -> List[float]:
        """
        商品通道指数（CCI）。
        """
        result = [0]
        length = len(kl_data)
        typ_data = self.typ(kl_data)
        typ_ma_data = self.sma(typ_data, day_count)
        type_ave_data = self.avedev(typ_data, day_count)
        for i in range(1, length):
            cci = (typ_data[i] - typ_ma_data[i]) / (0.015 * type_ave_data[i]) if type_ave_data[i] > 0 else 0
            result.append(cci)
        return result

    def get_week_line(self, kl_data: List[KLine]) -> List[dict]:
        """
        获取周线数据。
        """
        result = []
        data = {
            'time_key': '',
            'high': 0,
            'low': 0,
            'open': 0,
            'close': 0,
            'volume': 0
        }
        cur_week = ''
        index = -1
        for kdata in kl_data:
            week = kdata.time_key.strftime('%Y-%W')
            if cur_week != week:
                data = {
                    'time_key': kdata.time_key,
                    'high': kdata.high,
                    'low': kdata.low,
                    'open': kdata.open,
                    'close': kdata.close,
                    'volume': kdata.volume
                }
                index += 1
                cur_week = week
                result.append(data)
            else:
                data['high'] = max(data['high'], kdata['high'])
                data['low'] = min(data['low'], kdata['low'])
                data['close'] = kdata['close']
                data['volume'] += kdata['volume']
                result[index] = data
        return result
