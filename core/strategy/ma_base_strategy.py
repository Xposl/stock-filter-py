"""
MA均线策略模块
"""
from core.utils.utils import UtilsHelper
from core.strategy.base_strategy import BaseStrategy

class MaBaseStrategy(BaseStrategy):
    """MA均线策略实现类"""
    
    p1 = 13  # 短期均线周期
    p2 = 21  # 中期均线周期
    p3 = 55  # 长期均线周期

    def get_params(self):
        """获取策略参数

        Returns:
            dict: 策略参数字典
        """
        return {
            'p1': self.p1,
            'p2': self.p2,
            'p3': self.p3
        }

    def set_params(self, param):
        """设置策略参数

        Args:
            param: 参数字典
        """
        self.p1 = param['p1'] if 'p1' in param else self.p1
        self.p2 = param['p2'] if 'p2' in param else self.p2
        self.p3 = param['p3'] if 'p3' in param else self.p3

    def get_key(self):
        return 'MA_Base_strategy'
    
    def calculate(self, kl_data):
        """计算MA策略

        Args:
            kl_data: K线数据列表

        Returns:
            list: 策略仓位数据列表 [-1, 0, 1]
        """
        length = len(kl_data)
        close_data = []
        pos_data = []
        for kl_item in kl_data:
            close_data.append(kl_item['close'])
            
        ma_m = UtilsHelper().EMA(close_data, self.p2)
        ma_l = UtilsHelper().EMA(close_data, self.p3)
        
        status = 0
        for i in range(length):
            if i < 2:
                pos_data.append(0)
                continue
            
            close = close_data[i]
            slow_base = close_data[i - self.p1] if i - self.p1 > 0 else close_data[0]
            
            diff = (ma_l[i] - ma_l[i-1])/ma_l[i] if ma_l[i] > 0 else 0

            if diff > - 0.001 and ma_m[i-1] < ma_m[i] and close > slow_base:
                status = 1
            
            if diff < 0.001 and ma_m[i-1] > ma_m[i] and close <= slow_base:
                status = -1
            pos_data.append(status)
        
        return pos_data
