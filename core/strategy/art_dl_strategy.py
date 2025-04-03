"""
ART双线策略模块
"""
from core.utils import UtilsHelper

class ARTDLStrategy:
    """ART双线策略实现类"""
    
    day_count = 21
    multi = 6.3

    def get_key(self):
        """获取策略键名

        Returns:
            str: 策略键名
        """
        return 'ART_DL_strategy'

    def calculate(self, kl_data):
        """计算ART双线策略

        Args:
            kl_data: K线数据列表

        Returns:
            list: 策略仓位数据列表 [-1, 0, 1]
        """
        art_data = UtilsHelper().RATR(kl_data, self.day_count)
        loss_data = []
        close_data = []

        for kl_item in kl_data:
            close_data.append(kl_item['close'])

        for art_item in art_data:
            loss_data.append(art_item * self.multi)

        return UtilsHelper().doubleLinePos(close_data, close_data, loss_data)
