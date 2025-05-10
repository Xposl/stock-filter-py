"""
CCI-MACD策略模块
"""
from core.libs.utils import UtilsHelper
from core.strategy.base_strategy import BaseStrategy

class CCIMacdStrategy(BaseStrategy):
    """CCI-MACD趋势策略实现类"""
    
    cci_p1 = 13  # 短期CCI长度
    cci_p2 = 34  # 长期CCI长度
    cci_m = 9    # TED均线长度
    macd_short = 13  # MACD短期
    macd_long = 34   # MACD长期
    macd_m = 9       # MACD平滑
    day_wait = 2     # 连续上升/下降周期数

    def get_params(self):
        """获取策略参数

        Returns:
            dict: 策略参数字典
        """
        return {
            'cci_p1': self.cci_p1,
            'cci_p2': self.cci_p2,
            'cci_m': self.cci_m,
            'macd_short': self.macd_short,
            'macd_long': self.macd_long,
            'macd_m': self.macd_m,
            'day_wait': self.day_wait
        }

    def set_params(self, param):
        """设置策略参数

        Args:
            param: 参数字典
        """
        self.cci_p1 = param['cci_p1'] if 'cci_p1' in param else self.cci_p1
        self.cci_p2 = param['cci_p2'] if 'cci_p2' in param else self.cci_p2
        self.cci_m = param['cci_m'] if 'cci_m' in param else self.cci_m
        self.macd_short = param['macd_short'] if 'macd_short' in param else self.macd_short
        self.macd_long = param['macd_long'] if 'macd_long' in param else self.macd_long
        self.macd_m = param['macd_m'] if 'macd_m' in param else self.macd_m
        self.day_wait = param['day_wait'] if 'day_wait' in param else self.day_wait

    def get_key(self):
        """获取策略键名

        Returns:
            str: 策略键名
        """
        return 'CCI_MACD_strategy'
    
    def calculate(self, kl_data):
        """计算CCI-MACD策略

        Args:
            kl_data: K线数据列表

        Returns:
            list: 策略仓位数据列表 [-1, 0, 1]
        """
        length = len(kl_data)
        close_data = []
        pos_data = []
        utils = UtilsHelper()

        for kl_item in kl_data:
            close_data.append(kl_item['close'])
        
        # 计算CCI指标
        cci_1 = utils.CCI(kl_data, self.cci_p1)
        cci_2 = utils.CCI(kl_data, self.cci_p2)
        
        # 计算TED (CCI1 + CCI2的EMA)
        cci_sum = []
        for i in range(length):
            cci_sum.append(cci_1[i] + cci_2[i])
        
        ted = utils.EMA(cci_sum, self.cci_m)
        
        # 计算MACD
        ema_short = utils.EMA(close_data, self.macd_short)
        ema_long = utils.EMA(close_data, self.macd_long)
        
        dif = []
        for i in range(length):
            dif.append(ema_short[i] - ema_long[i])
        
        dea = utils.EMA(dif, self.macd_m)
        
        macd = []
        for i in range(length):
            macd.append((dif[i] - dea[i]) * 2)
        
        # 记录前一周期指标值，用于判断方向
        prev_ted = [0]
        prev_macd = [0]
        
        for i in range(1, length):
            prev_ted.append(ted[i-1])
            prev_macd.append(macd[i-1])
        
        # 计算仓位
        status = 0
        for i in range(length):
            if i < self.day_wait:
                pos_data.append(0)
                continue
            
            # 判断TED和MACD的方向是否一致
            ted_up = ted[i] > prev_ted[i]
            macd_up = macd[i] > prev_macd[i]
            ted_down = ted[i] < prev_ted[i]
            macd_down = macd[i] < prev_macd[i]
            
            # 一致的方向
            direction_up = ted_up and macd_up
            direction_down = ted_down and macd_down
            
            
            # 判断CCI指标是否连续上升/下降
            # 检查是否连续上升self.day_wait个周期
            cci_up_trend = True
            for j in range(1, self.day_wait + 1):
                if i-j < 0 or cci_sum[i-j+1] <= cci_sum[i-j]:
                    cci_up_trend = False
                    break
            
            # 检查是否连续下降self.day_wait个周期
            cci_down_trend = True
            for j in range(1, self.day_wait + 1):
                if i-j < 0 or cci_sum[i-j+1] >= cci_sum[i-j]:
                    cci_down_trend = False
                    break
            
            # 买入条件: TED和MACD其中一个大于0，且两个指标方向一致，CCI指标连续上升至少2个周期
            buy = direction_up and cci_up_trend
            
            # 卖出条件: TED和MACD其中一个小于0，且两个指标方向一致，CCI指标连续下降至少2个周期
            sell = direction_down and cci_down_trend
            
            if buy:
                status = 1
            
            if sell:
                status = -1
                
            pos_data.append(status)
            
        return pos_data
