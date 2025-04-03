"""
布林带双线策略模块
"""
from core.utils import UtilsHelper

class BollDLStrategy:
    """布林带双线策略实现类"""
    
    day_count = 21
    multi = 2

    def get_key(self):
        """获取策略键名

        Returns:
            str: 策略键名
        """
        return 'BOLL_DL_strategy'

    def calculate(self, kl_data):
        """计算布林带双线策略

        Args:
            kl_data: K线数据列表

        Returns:
            list: 策略仓位数据列表 [-1, 0, 1]
        """
        loss_data = []
        close_data = []

        for kl_item in kl_data:
            close_data.append(kl_item['close'])

        sma_data = UtilsHelper().SMA(close_data, self.day_count)
        dev_data = UtilsHelper().STDDEV(close_data, self.day_count)

        for dev_item in dev_data:
            loss_data.append(dev_item * self.multi)

        return UtilsHelper().doubleLinePos(close_data, sma_data, dev_data)
