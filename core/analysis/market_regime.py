import numpy as np
import pandas as pd
from enum import Enum

class MarketRegime(Enum):
    BULL = 1    # 牛市
    BEAR = -1   # 熊市
    RANGE = 0   # 震荡市
    STRONG_BULL = 2  # 强势牛市 
    STRONG_BEAR = -2 # 强势熊市

class MarketRegimeClassifier:
    """市场环境分类器"""
    
    def __init__(self, sma_period=200, volatility_period=20, bull_threshold=0.05, bear_threshold=-0.05,
                 rsi_period=14, volume_ma_period=20, macd_fast=12, macd_slow=26, macd_signal=9):
        """
        初始化市场环境分类器
        
        参数:
        sma_period: 简单移动平均的周期
        volatility_period: 波动率计算的周期
        bull_threshold: 牛市判定的阈值
        bear_threshold: 熊市判定的阈值
        rsi_period: RSI指标周期
        volume_ma_period: 成交量移动平均周期
        macd_fast: MACD快线周期
        macd_slow: MACD慢线周期
        macd_signal: MACD信号线周期
        """
        self.sma_period = sma_period
        self.volatility_period = volatility_period
        self.bull_threshold = bull_threshold
        self.bear_threshold = bear_threshold
        self.rsi_period = rsi_period
        self.volume_ma_period = volume_ma_period
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
    
    def classify(self, kl_data):
        """对K线数据进行市场环境分类"""
        # 转换为DataFrame处理
        if not isinstance(kl_data, pd.DataFrame):
            df = pd.DataFrame(kl_data)
        else:
            df = kl_data.copy()
        
        # 确保至少有足够的数据
        min_periods = max(self.sma_period, self.volatility_period, self.rsi_period)
        if len(df) < min_periods:
            return [MarketRegime.RANGE] * len(df)
        
        # 计算基础技术指标
        df['close'] = pd.to_numeric(df['close'])
        df['volume'] = pd.to_numeric(df['volume'])
        df['sma'] = df['close'].rolling(window=self.sma_period).mean()
        df['price_to_sma'] = df['close'] / df['sma'] - 1
        
        # 计算波动率
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(window=self.volatility_period).std()
        
        # 计算RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 计算成交量相关指标
        df['volume_ma'] = df['volume'].rolling(window=self.volume_ma_period).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        # 计算MACD
        exp1 = df['close'].ewm(span=self.macd_fast, adjust=False).mean()
        exp2 = df['close'].ewm(span=self.macd_slow, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['signal'] = df['macd'].ewm(span=self.macd_signal, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['signal']
        
        # 计算市场强度指标
        df['market_strength'] = self._calculate_market_strength(df)
        
        # 市场环境分类
        regimes = []
        
        for i in range(len(df)):
            if i < min_periods:
                regimes.append(MarketRegime.RANGE)
                continue
            
            # 获取当前指标值
            price_to_sma = df.iloc[i]['price_to_sma']
            rsi = df.iloc[i]['rsi']
            volume_ratio = df.iloc[i]['volume_ratio']
            market_strength = df.iloc[i]['market_strength']
            macd_hist = df.iloc[i]['macd_hist']
            
            # 综合判断市场状态
            if price_to_sma > self.bull_threshold:
                if market_strength > 0.8 and rsi > 70 and volume_ratio > 1.5:
                    regimes.append(MarketRegime.STRONG_BULL)
                else:
                    regimes.append(MarketRegime.BULL)
            elif price_to_sma < self.bear_threshold:
                if market_strength < 0.2 and rsi < 30 and volume_ratio > 1.5:
                    regimes.append(MarketRegime.STRONG_BEAR)
                else:
                    regimes.append(MarketRegime.BEAR)
            else:
                regimes.append(MarketRegime.RANGE)
        
        return regimes
    
    def _calculate_market_strength(self, df):
        """计算市场强度指标 (0-1之间)"""
        # 计算多个分项指标并归一化
        
        # 1. 趋势强度 (基于价格与均线关系)
        trend_strength = (df['close'] - df['sma']).abs() / df['sma']
        trend_strength = trend_strength / trend_strength.max()
        
        # 2. 成交量强度
        volume_strength = df['volume_ratio']
        volume_strength = volume_strength / volume_strength.max()
        
        # 3. RSI强度 (将RSI从0-100转换为0-1)
        rsi_strength = df['rsi'] / 100
        
        # 4. MACD强度
        macd_strength = df['macd_hist'].abs()
        macd_strength = macd_strength / macd_strength.max()
        
        # 5. 波动率强度
        volatility_strength = df['volatility']
        volatility_strength = volatility_strength / volatility_strength.max()
        
        # 综合计算市场强度 (加权平均)
        market_strength = (
            trend_strength * 0.3 +
            volume_strength * 0.2 +
            rsi_strength * 0.2 +
            macd_strength * 0.2 +
            volatility_strength * 0.1
        )
        
        return market_strength
    
    def analyze_strategy_by_regime(self, strategy_trades, kl_data):
        """分析策略在不同市场环境下的表现"""
        regimes = self.classify(kl_data)
        
        # 将分类结果转换为字典，便于查找
        regime_dict = {}
        for i, regime in enumerate(regimes):
            date = kl_data[i]['time_key']
            if isinstance(date, str):
                date = pd.to_datetime(date)
            regime_dict[date] = regime
        
        # 按市场环境分类交易
        strong_bull_trades = []
        bull_trades = []
        bear_trades = []
        strong_bear_trades = []
        range_trades = []
        
        for trade in strategy_trades:
            entry_date = trade['entry_date']
            if isinstance(entry_date, str):
                entry_date = pd.to_datetime(entry_date)
                
            # 找到最接近的日期
            closest_date = min(regime_dict.keys(), key=lambda x: abs(x - entry_date))
            regime = regime_dict.get(closest_date)
            
            if regime == MarketRegime.STRONG_BULL:
                strong_bull_trades.append(trade)
            elif regime == MarketRegime.BULL:
                bull_trades.append(trade)
            elif regime == MarketRegime.BEAR:
                bear_trades.append(trade)
            elif regime == MarketRegime.STRONG_BEAR:
                strong_bear_trades.append(trade)
            else:
                range_trades.append(trade)
        
        # 计算每种环境下的表现
        results = {}
        
        for label, trades, regime in [
            ('strong_bull', strong_bull_trades, MarketRegime.STRONG_BULL),
            ('bull', bull_trades, MarketRegime.BULL),
            ('bear', bear_trades, MarketRegime.BEAR),
            ('strong_bear', strong_bear_trades, MarketRegime.STRONG_BEAR),
            ('range', range_trades, MarketRegime.RANGE)
        ]:
            if len(trades) == 0:
                continue
                
            win_trades = len([t for t in trades if t['profit'] > 0])
            total_profit = sum(t['profit'] for t in trades)
            
            # 计算额外的性能指标
            profits = [t['profit'] for t in trades]
            holding_days = [(pd.to_datetime(t['exit_date']) - pd.to_datetime(t['entry_date'])).days for t in trades]
            
            results[label] = {
                'regime': regime,
                'trade_count': len(trades),
                'win_count': win_trades,
                'win_rate': win_trades / len(trades) if len(trades) > 0 else 0,
                'total_profit': total_profit,
                'avg_profit': total_profit / len(trades) if len(trades) > 0 else 0,
                'max_profit': max(profits) if profits else 0,
                'max_loss': min(profits) if profits else 0,
                'profit_std': np.std(profits) if profits else 0,
                'avg_holding_days': np.mean(holding_days) if holding_days else 0,
                'trades': trades
            }
        
        # 添加市场环境统计信息
        regime_counts = pd.Series(regimes).value_counts()
        results['regime_stats'] = {str(regime): count for regime, count in regime_counts.items()}
        
        return results
