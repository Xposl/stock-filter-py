"""
CCI-WMA策略模块
"""
from core.utils import UtilsHelper

class CCIWmaStrategy:
    """CCI-WMA趋势策略实现类"""
    
    cci_s_len = 13  # 短期CCI长度
    cci_m_len = 21  # 中期CCI长度
    cci_l_len = 34  # 长期CCI长度
    day_wait = 2    # 等待天数

    def get_params(self):
        """获取策略参数

        Returns:
            dict: 策略参数字典
        """
        return {
            'cci_s_len': self.cci_s_len,
            'cci_m_len': self.cci_m_len,
            'cci_l_len': self.cci_l_len,
            'day_wait': self.day_wait
        }

    def set_params(self, param):
        """设置策略参数

        Args:
            param: 参数字典
        """
        self.cci_s_len = param['cci_s_len'] if 'cci_s_len' in param else self.cci_s_len
        self.cci_m_len = param['cci_m_len'] if 'cci_m_len' in param else self.cci_m_len
        self.cci_l_len = param['cci_l_len'] if 'cci_l_len' in param else self.cci_l_len
        self.day_wait = param['day_wait'] if 'day_wait' in param else self.day_wait

    def get_key(self):
        """获取策略键名

        Returns:
            str: 策略键名
        """
        return 'CCI_WMA_strategy'
    
    def calculate(self, kl_data):
        """计算CCI-WMA策略

        Args:
            kl_data: K线数据列表

        Returns:
            list: 策略仓位数据列表 [-1, 0, 1]
        """
        length = len(kl_data)
        close_data = []
        stop_data = [0, 0]
        pos_data = []

        for kl_item in kl_data:
            close_data.append(kl_item['close'])
            
        cci_s = UtilsHelper().CCI(kl_data, self.cci_s_len)
        cci_m = UtilsHelper().CCI(kl_data, self.cci_m_len)
        cci_l = UtilsHelper().CCI(kl_data, self.cci_l_len)

        ma_s = UtilsHelper().WMA(close_data, self.cci_s_len)
        ma_m = UtilsHelper().WMA(close_data, self.cci_m_len)
        ma_l = UtilsHelper().WMA(close_data, self.cci_l_len)

        # 计算趋势停损点
        for i in range(2, len(kl_data)):
            is_short = -1 if ma_m[i-2] > ma_l[i-2] and ma_m[i-1] <= ma_l[i-1] else stop_data[i-1]
            is_long = 1 if ma_s[i-2] < ma_m[i-2] and ma_s[i-1] >= ma_m[i-1] else is_short
            stop_data.append(is_long)
        
        status = 0
        for i in range(length):
            # 检查各周期CCI趋势
            cci_up_s = UtilsHelper().keepUpTrend(cci_s, 100, i, self.day_wait)
            cci_up_m = UtilsHelper().keepUpTrend(cci_m, -100, i, self.day_wait)
            cci_up_l = UtilsHelper().keepUpTrend(cci_l, -100, i, self.day_wait)
            cci_down_s = UtilsHelper().keepDownTrend(cci_s, -100, i, self.day_wait)
            cci_down_m = UtilsHelper().keepDownTrend(cci_m, 100, i, self.day_wait)
            cci_down_l = UtilsHelper().keepDownTrend(cci_l, 100, i, self.day_wait)

            # 合成多空信号
            cci_long = cci_up_s and cci_up_m and cci_up_l
            cci_short = cci_down_s and cci_down_m and cci_down_l

            buy = cci_long and stop_data[i] == 1
            sell = cci_short and stop_data[i] == -1

            if buy:
                status = 1
            
            if sell:
                status = -1
                
            pos_data.append(status)
            
        return pos_data
