"""
Volume SuperTrend AI策略模块
"""
from core.strategy.base_strategy import BaseStrategy
from core.indicator.volume_supertrend_ai_indicator import VolumeSuperTrendAIIndicator
from core.libs.utils import UtilsHelper

class VolumeSuperTrendAIStrategy(BaseStrategy):
    """Volume SuperTrend AI策略实现类"""
    
    # SuperTrend参数
    len = 21
    factor = 3.0
    maSrc = "WMA"
    
    # KNN参数
    k = 3
    n = 10
    KNN_PriceLen = 20
    KNN_STLen = 100
    
    # 策略参数
    volume_filter = True      # 是否启用成交量过滤
    volume_threshold = 1.5    # 成交量门限(相对于均值)
    confirm_days = 2          # 信号确认天数
    trend_filter = True       # 是否启用趋势过滤
    ma_period = 50            # 趋势判断移动平均周期

    def __init__(self, len=10, factor=3.0, maSrc="WMA", k=3, n=10, KNN_PriceLen=20, KNN_STLen=100,
                 volume_filter=True, volume_threshold=1.5, confirm_days=2, trend_filter=True, ma_period=50):
        """初始化策略参数

        Args:
            len (int): SuperTrend长度
            factor (float): SuperTrend乘数
            maSrc (str): 移动平均类型，可选["SMA", "EMA", "WMA", "RMA", "VWMA"]
            k (int): KNN算法邻居数量
            n (int): 考虑的数据点数量
            KNN_PriceLen (int): 价格趋势长度
            KNN_STLen (int): 预测趋势长度
            volume_filter (bool): 是否启用成交量过滤
            volume_threshold (float): 成交量门限(相对于均值)
            confirm_days (int): 信号确认天数
            trend_filter (bool): 是否启用趋势过滤
            ma_period (int): 趋势判断移动平均周期
        """
        self.len = len
        self.factor = factor
        self.maSrc = maSrc
        self.k = k
        self.n = max(k, n)
        self.KNN_PriceLen = KNN_PriceLen
        self.KNN_STLen = KNN_STLen
        self.volume_filter = volume_filter
        self.volume_threshold = volume_threshold
        self.confirm_days = confirm_days
        self.trend_filter = trend_filter
        self.ma_period = ma_period
        self.indicator = VolumeSuperTrendAIIndicator(
            len=self.len,
            factor=self.factor,
            maSrc=self.maSrc,
            k=self.k,
            n=self.n,
            KNN_PriceLen=self.KNN_PriceLen,
            KNN_STLen=self.KNN_STLen
        )

    def get_params(self):
        """获取策略参数

        Returns:
            dict: 策略参数字典
        """
        return {
            'len': self.len,
            'factor': self.factor,
            'maSrc': self.maSrc,
            'k': self.k,
            'n': self.n,
            'KNN_PriceLen': self.KNN_PriceLen,
            'KNN_STLen': self.KNN_STLen,
            'volume_filter': self.volume_filter,
            'volume_threshold': self.volume_threshold,
            'confirm_days': self.confirm_days,
            'trend_filter': self.trend_filter,
            'ma_period': self.ma_period
        }

    def set_params(self, param):
        """设置策略参数

        Args:
            param (dict): 参数字典
        """
        self.len = param['len'] if 'len' in param else self.len
        self.factor = param['factor'] if 'factor' in param else self.factor
        self.maSrc = param['maSrc'] if 'maSrc' in param else self.maSrc
        self.k = param['k'] if 'k' in param else self.k
        self.n = max(self.k, param['n'] if 'n' in param else self.n)
        self.KNN_PriceLen = param['KNN_PriceLen'] if 'KNN_PriceLen' in param else self.KNN_PriceLen
        self.KNN_STLen = param['KNN_STLen'] if 'KNN_STLen' in param else self.KNN_STLen
        self.volume_filter = param['volume_filter'] if 'volume_filter' in param else self.volume_filter
        self.volume_threshold = param['volume_threshold'] if 'volume_threshold' in param else self.volume_threshold
        self.confirm_days = param['confirm_days'] if 'confirm_days' in param else self.confirm_days
        self.trend_filter = param['trend_filter'] if 'trend_filter' in param else self.trend_filter
        self.ma_period = param['ma_period'] if 'ma_period' in param else self.ma_period
        
        # 更新指标参数
        self.indicator = VolumeSuperTrendAIIndicator(
            len=self.len,
            factor=self.factor,
            maSrc=self.maSrc,
            k=self.k,
            n=self.n,
            KNN_PriceLen=self.KNN_PriceLen,
            KNN_STLen=self.KNN_STLen
        )

    def get_key(self):
        """获取策略键名

        Returns:
            str: 策略键名
        """
        return 'Volume_SuperTrend_AI_strategy'
    
    def calculate(self, kl_data):
        """计算Volume SuperTrend AI策略

        Args:
            kl_data (list): K线数据列表

        Returns:
            list: 策略仓位数据列表 [-1, 0, 1]
        """
        length = len(kl_data)
        if length < max(self.len, self.KNN_PriceLen, self.KNN_STLen, self.ma_period) + self.n:
            # 数据不足
            return [0] * length
        
        # 获取指标数据
        indicator_result = self.indicator.calculate(kl_data)
        indicator_pos_data = indicator_result['posData']
        
        # 准备数据
        closeData = []
        volumeData = []
        for klItem in kl_data:
            closeData.append(klItem['close'])
            volumeData.append(klItem['volume'])
        
        # 计算成交量均值用于过滤
        utils = UtilsHelper()
        volume_ma = utils.SMA(volumeData, 20)
        
        # 计算长期趋势用于过滤
        if self.trend_filter:
            ma_long = utils.EMA(closeData, self.ma_period)
        
        # 生成交易信号
        pos_data = []
        current_pos = 0
        
        for i in range(length):
            if i < self.confirm_days:
                pos_data.append(0)
                continue
            
            # 获取指标信号
            indicator_signal = indicator_pos_data[i]
            
            # # 1. 验证信号持续性(信号确认)
            # signal_confirmed = True
            # if self.confirm_days > 0:
            #     for j in range(1, self.confirm_days + 1):
            #         if i - j >= 0 and indicator_pos_data[i - j] != indicator_signal:
            #             signal_confirmed = False
            #             break
            
            # # 2. 成交量过滤
            # volume_ok = True
            # if self.volume_filter and i > 20:  # 确保有足够的数据计算均值
            #     if indicator_signal != 0 and volumeData[i] < volume_ma[i] * self.volume_threshold:
            #         volume_ok = False
            
            # # 3. 趋势过滤
            # trend_ok = True
            # if self.trend_filter and i > self.ma_period:
            #     price_trend = 1 if closeData[i] > ma_long[i] else -1
            #     # 只在顺趋势方向交易
            #     if indicator_signal == 1 and price_trend == -1:
            #         trend_ok = False
            #     elif indicator_signal == -1 and price_trend == 1:
            #         trend_ok = False
            
            # # 应用信号
            # if signal_confirmed and volume_ok and trend_ok:
            #     if indicator_signal != 0:
            #         current_pos = indicator_signal
            
            pos_data.append(indicator_signal)
        
        return pos_data
    
    def _detect_ai_signal(self, indicator_pos_data, i):
        """检测AI特殊信号点
        模拟TradingView原始代码中的AI信号检测逻辑
        
        Args:
            indicator_pos_data: 指标方向数据
            i: 当前索引
            
        Returns:
            tuple: (是否有信号, 信号方向)
        """
        if i < 2:
            return False, 0
            
        # 检测AI看涨趋势开始 (当前信号为多头，前一信号不是多头)
        if (indicator_pos_data[i] == 1 and 
            (indicator_pos_data[i-1] != 1)):
            return True, 1
            
        # 检测AI看跌趋势开始 (当前信号为空头，前一信号不是空头)
        if (indicator_pos_data[i] == -1 and 
            (indicator_pos_data[i-1] != -1)):
            return True, -1
            
        return False, 0
