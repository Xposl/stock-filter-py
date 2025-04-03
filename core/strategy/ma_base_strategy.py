from core.utils import UtilsHelper

class MABaseStrategy:
    p1 = 13
    p2 = 21
    p3 = 55

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
