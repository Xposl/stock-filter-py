"""
CCI-MA策略模块
"""
from core.utils import UtilsHelper
from core.strategy.base_strategy import BaseStrategy

class CCIMaStrategy(BaseStrategy):
    """CCI-MA趋势策略实现类"""
    
    cci_s_len = 13   # 短期CCI长度
    cci_m_len = 21   # 中期CCI长度
    cci_l_len = 34   # 长期CCI长度
    day_wait = 2     # 等待天数
    vol_ma = 20      # 成交量MA周期
    vol_ratio = 1.2  # 成交量放大倍数

    def get_params(self):
        """获取策略参数

        Returns:
            dict: 策略参数字典
        """
        return {
            'cci_s_len': self.cci_s_len,    # 短期CCI周期
            'cci_m_len': self.cci_m_len,    # 中期CCI周期
            'cci_l_len': self.cci_l_len,    # 长期CCI周期
            'day_wait': self.day_wait,       # 确认等待天数
            'vol_ma': self.vol_ma,          # 成交量MA周期
            'vol_ratio': self.vol_ratio     # 成交量放大倍数
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
        self.vol_ma = param['vol_ma'] if 'vol_ma' in param else self.vol_ma
        self.vol_ratio = param['vol_ratio'] if 'vol_ratio' in param else self.vol_ratio

    def get_key(self):
        """获取策略键名

        Returns:
            str: 策略键名
        """
        return 'CCI_MA_strategy'
    
    def calculate(self, kl_data):
        """计算CCI-MA策略

        Args:
            kl_data: K线数据列表

        Returns:
            list: 策略仓位数据列表 [-1, 0, 1]
        """
        length = len(kl_data)
        close_data = []
        volume_data = []
        pos_data = []
        for kl_item in kl_data:
            close_data.append(kl_item['close'])
            volume_data.append(kl_item['volume'])
            
        cci_s = UtilsHelper().CCI(kl_data, self.cci_s_len)
        cci_m = UtilsHelper().CCI(kl_data, self.cci_m_len)
        cci_l = UtilsHelper().CCI(kl_data, self.cci_l_len)

        ma_l = UtilsHelper().HMA(close_data, self.cci_l_len)
        vol_ma = UtilsHelper().SMA(volume_data, self.vol_ma)
        
        condi_data = []
        v2_data = []
        status = 0
        
        for i in range(length):
            cci_ts = UtilsHelper().keepUpTrend(cci_s, 0, i, 2)
            cci_tm = UtilsHelper().keepUpTrend(cci_m, 0, i, 2)
            cci_tl = UtilsHelper().keepUpTrend(cci_l, 0, i, 2)
            
            # 计算趋势值
            v1 = cci_s[i] if cci_ts else cci_s[i] - 100
            v2 = cci_m[i] if cci_tm else v1
            condi = cci_l[i] if cci_tl else v2
            v2_data.append(v2)
            condi_data.append(condi)

            if i < self.cci_s_len:
                pos_data.append(0)
                continue

            buy = UtilsHelper().keepUpTrend(condi_data, 0, i, self.day_wait)
            sell = UtilsHelper().keepDownTrend(condi_data, -100, i, self.day_wait)

            ma_d = ma_l[i] - ma_l[i-self.cci_l_len] if i-self.cci_l_len > 0 else ma_l[i] - ma_l[0]
            ma_d = ma_d/ma_l[i] > -0.03 if ma_l[i] is not None and ma_l[i] > 0 else True
            
            # 成交量确认
            vol_confirm = False
            if i >= 1:
                # 判断成交量是否超过均线，且较前一日放大
                vol_confirm = (volume_data[i] > vol_ma[i] * self.vol_ratio and 
                             volume_data[i] > volume_data[i-1])

            # 买入条件：趋势向上 + 价格突破 + 均线向上 + 成交量确认
            if buy and close_data[i] >= close_data[i-self.cci_s_len] and ma_d and vol_confirm:
                status = 1
            
            # 卖出条件：趋势向下 + 价格破位
            if sell and close_data[i] < close_data[i-self.cci_s_len]:
                status = -1

            pos_data.append(status)
            
        return pos_data
