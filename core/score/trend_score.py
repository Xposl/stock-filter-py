from typing import Optional
from core.indicator import Indicator as Helper
from core.enum.indicator_group import IndicatorGroup
import numpy as np
from scipy import stats

from core.models.ticker import Ticker

class TrendScore:
    """
    改进的趋势评分系统，针对做多股票选择优化
    主要改进：
    1. 考虑趋势的强度和持续性
    2. 动态调整指标权重（用于评分计算，不影响信号计数）
    3. 引入时间衰减因子，增加最近信号的重要性
    4. 考虑价格和成交量的确认关系
    5. 增强策略影响因子
    """

    def __init__(self):
        # 参数配置
        self.trend_window = 20  # 趋势计算窗口
        self.time_decay_factor = 0.95  # 时间衰减因子
        self.min_data_points = 30  # 最小数据点数，用于Z分数计算
        self.time_decay_window = 10  # 时间衰减应用窗口（最近N天的信号权重更高）

    def calculate(self, ticker: Ticker, kLineData: Optional[list]=None, strategyData: Optional[list]=None, indicatorData: Optional[list]=None, valuationData: Optional[list]=None):
        """
        计算趋势增强型评分
        
        Args:
            ticker: 股票信息
            kLineData: K线数据
            strategyData: 策略数据
            indicatorData: 指标数据
            valuationData: 估值数据
            
        Returns:
            包含评分的结果列表
        """
        tickerId = ticker.id
        length = len(kLineData)
        if length == 0:
            print('无数据')
            return
        
        # 初始化结果数组
        result = []
        for i in range(length):
            result.append({
                'id': kLineData[i].get('id', 0),  # 使用get方法，如果没有id键则默认为0
                'time_key': kLineData[i]['time_key'].strftime('%Y-%m-%d') if hasattr(kLineData[i]['time_key'], 'strftime') else kLineData[i]['time_key'],
                'ticker_id': tickerId,
                'ma_buy': 0.0,  # 浮点型，表示买入信号强度
                'ma_sell': 0.0,  # 浮点型，表示卖出信号强度
                'ma_score': 0.0,
                'in_buy': 0.0,  # 浮点型，表示买入信号强度
                'in_sell': 0.0,  # 浮点型，表示卖出信号强度
                'in_score': 0.0,
                'strategy_buy': 0,
                'strategy_sell': 0,
                'strategy_score': 0.0,
                'trend_strength': 0.0,
                'trend_persistence': 0.0,
                'volume_price_confirm': 0.0,
                'score': 0.0,
                'raw_score': 0.0
            })
        
        # 1. 计算基础指标买卖信号统计（与原始系统类似）
        maTotal = 0
        inTotal = 0
        strategyTotal = len(strategyData)
        
        # 统计策略买卖信号（整数）
        for strategyKey in strategyData:
            strategy = strategyData[strategyKey]
            posData = strategy['pos_data']
            for i in range(length):
                result[i]['strategy_buy'] += 1 if posData[i] == 1 else 0  # 整数
                result[i]['strategy_sell'] += 1 if posData[i] == -1 else 0  # 整数
        
        # 计算指标重要性权重（仅用于最终评分计算）
        indicator_weights = self._calculate_indicator_weights(indicatorData, kLineData)
        
        # 处理指标数据 - 直接使用加权信号
        for indicatorKey in indicatorData:
            indicator = indicatorData[indicatorKey]
            history = indicator['history']
            group = IndicatorGroup(Helper().getGroupByKey(indicatorKey))
            
            # 计数用于总数统计
            if group == IndicatorGroup.BASE:
                maTotal += 1
            elif group == IndicatorGroup.POWER:
                inTotal += 1

            # 应用时间衰减
            decayed_history = self._apply_time_decay(history)
            
            # 获取指标权重
            weight = indicator_weights.get(indicatorKey, 1.0)
            
            # 为结果记录加权后的信号强度
            for i in range(length):
                signal = decayed_history[i] if i < len(decayed_history) else 0
                
                # 根据信号的方向和强度计算加权值
                if signal != 0:
                    # 计算加权信号强度
                    weighted_signal = signal * weight
                    
                    if group == IndicatorGroup.BASE:
                        if signal > 0:
                            result[i]['ma_buy'] += weighted_signal  # 加权浮点值
                        elif signal < 0:
                            result[i]['ma_sell'] -= weighted_signal  # 加权浮点值（取负数的相反数）
                    elif group == IndicatorGroup.POWER:
                        if signal > 0:
                            result[i]['in_buy'] += weighted_signal  # 加权浮点值
                        elif signal < 0:
                            result[i]['in_sell'] -= weighted_signal  # 加权浮点值（取负数的相反数）
        
        # 2. 计算趋势强度
        trend_strength, trend_persistence = self._calculate_trend_factors(kLineData)
        
        # 3. 计算价格-交易量确认因子
        volume_price_factors = self._calculate_volume_price_confirmation(kLineData)
        
        # 收集原始分数
        raw_scores = []
        
        # 4. 整合所有因子，计算最终评分
        for i in range(length):
            # 标准化买卖信号强度，使其在-1到1之间
            maV = (result[i]['ma_buy'] - result[i]['ma_sell']) / maTotal if maTotal > 0 else 0
            inV = (result[i]['in_buy'] - result[i]['in_sell']) / inTotal if inTotal > 0 else 0
            
            # 确保值在-1到1之间
            maV = max(-1.0, min(1.0, maV))
            inV = max(-1.0, min(1.0, inV))
            
            # 保留传统评分用于参考
            result[i]['ma_score'] = maV * 50 + 50
            result[i]['in_score'] = inV * 50 + 50
            result[i]['strategy_score'] = (result[i]['strategy_buy'] - result[i]['strategy_sell']) / strategyTotal * 50 + 50 if strategyTotal > 0 else 50
            
            # 记录趋势因子（用于参考）
            if i < len(trend_strength):
                result[i]['trend_strength'] = float(format(trend_strength[i], '.4f'))
            if i < len(trend_persistence):
                result[i]['trend_persistence'] = float(format(trend_persistence[i], '.4f'))
            if i < len(volume_price_factors):
                result[i]['volume_price_confirm'] = float(format(volume_price_factors[i], '.4f'))
            
            # 增强的策略影响因子
            strategy_factor = self._calculate_enhanced_strategy_factor(result[i])
            
            # 计算原始评分（不受限的）
            # 指标基础评分 (40%)
            base_score = (maV + inV) / 2 * 0.4
            
            # 趋势强度 (20%)
            ts = trend_strength[i] if i < len(trend_strength) else 0
            trend_score = ts * 0.2
            
            # 趋势持续性 (15%)
            tp = trend_persistence[i] if i < len(trend_persistence) else 0
            persistence_score = tp * 0.15
            
            # 策略因子 (15%)
            strategy_score = strategy_factor * 0.15
            
            # 价格-交易量确认 (10%)
            pv = volume_price_factors[i] if i < len(volume_price_factors) else 0
            pv_score = pv * 0.1
            
            # 组合最终得分
            raw_score = base_score + trend_score + persistence_score + strategy_score + pv_score
            
            # 保存原始评分
            result[i]['raw_score'] = float(format(raw_score, '.4f'))
            raw_scores.append(raw_score)
        
        # 5. 计算Z分数（如果数据量足够）
        if len(raw_scores) > self.min_data_points:
            mean_score = np.mean(raw_scores)
            std_score = np.std(raw_scores) if np.std(raw_scores) > 0 else 1.0
            
            for i in range(length):
                z_score = (result[i]['raw_score'] - mean_score) / std_score
                result[i]['z_score'] = float(format(z_score, '.4f'))
                # 将Z分数转换为百分位数 (0-100)
                percentile = stats.norm.cdf(z_score) * 100
                result[i]['score'] = float(format(percentile, '.4f'))
        else:
            # 数据量不足时使用简单归一化
            min_score = min(raw_scores) if raw_scores else 0
            max_score = max(raw_scores) if raw_scores else 1
            score_range = max_score - min_score if max_score > min_score else 1
            
            for i in range(length):
                normalized = (result[i]['raw_score'] - min_score) / score_range * 100
                result[i]['score'] = float(format(max(0, min(100, normalized)), '.4f'))
        
        return result
    
    def _calculate_indicator_weights(self, indicator_data: Optional[list]=None, kLineData: Optional[list]=None):
        """
        计算每个指标的权重，基于其历史准确率或特性
        
        简化版实现：对不同类型的指标分配不同基本权重
        """
        weights = {}
        # 假设我们有一个指标表现数据，这里简单模拟
        for indicator_key in indicator_data:
            # 这里可以基于历史表现动态计算权重
            # 简化实现：根据指标类型给予不同权重
            if 'MACD' in indicator_key:
                weights[indicator_key] = 1.2  # 增强MACD权重
            elif 'RSI' in indicator_key:
                weights[indicator_key] = 1.1  # 增强RSI权重
            elif 'KDJ' in indicator_key:
                weights[indicator_key] = 1.0  # 标准权重
            elif 'SMA' in indicator_key or 'EMA' in indicator_key:
                weights[indicator_key] = 0.9  # 降低简单均线权重
            else:
                weights[indicator_key] = 1.0  # 默认权重
        
        return weights
    
    def _apply_time_decay(self, signals):
        """
        应用时间衰减因子，使最近的信号具有更高权重
        
        Args:
            signals: 原始信号列表
            
        Returns:
            应用时间衰减后的信号列表
        """
        if not signals:
            return []
        
        decayed_signals = signals.copy()  # 创建原始信号的副本
        
        # 只对最近的self.time_decay_window个数据点应用时间衰减
        if len(signals) > self.time_decay_window:
            # 计算衰减权重（越靠前的数据点权重越小）
            for i in range(len(signals) - self.time_decay_window, len(signals)):
                # 计算这个数据点距离最近一个点有多远
                distance_from_end = len(signals) - 1 - i
                # 应用指数衰减（保持符号不变）
                decay_weight = self.time_decay_factor ** distance_from_end
                
                # 仅当信号不为0时应用衰减
                if signals[i] != 0:
                    # 保持信号的符号，但减小其幅度
                    signal_value = signals[i]
                    if i < len(signals) - self.time_decay_window // 2:
                        # 对较远的点，减弱信号
                        decayed_signals[i] = signal_value * decay_weight
                    else:
                        # 对较近的点，增强信号
                        amplification = 1 + (1 - decay_weight)
                        decayed_signals[i] = signal_value * amplification
        
        return decayed_signals
    
    def _calculate_trend_factors(self, kLineData: Optional[list]=None):
        """
        计算趋势强度和持续性
        
        Returns:
            tuple: (趋势强度列表, 趋势持续性列表)
        """
        if not kLineData:
            return [], []
            
        closes = [item['close'] for item in kLineData]
        volumes = [item['volume'] for item in kLineData]
        
        trend_strength = []
        trend_persistence = []
        
        # 计算趋势强度 (基于价格变化率和成交量支持)
        for i in range(self.trend_window, len(closes)):
            # 计算价格变化率
            price_change_rate = (closes[i] - closes[i-self.trend_window]) / closes[i-self.trend_window]
            
            # 计算成交量变化
            volume_factor = 1.0
            if i > 0 and volumes[i] > volumes[i-1]:
                # 成交量增加增强趋势信号
                volume_factor = 1.2
            
            # 价格变化与成交量因子结合
            strength = price_change_rate * volume_factor
            trend_strength.append(strength)
        
        # 填充前面的数据点
        trend_strength = [0] * self.trend_window + trend_strength
        
        # 计算趋势持续性 (连续上涨/下跌天数)
        current_trend = 0
        max_trend_value = 10  # 最大趋势值限制
        
        for i in range(1, len(closes)):
            if closes[i] > closes[i-1]:
                # 价格上涨
                current_trend = current_trend + 1 if current_trend >= 0 else 1
            elif closes[i] < closes[i-1]:
                # 价格下跌
                current_trend = current_trend - 1 if current_trend <= 0 else -1
            else:
                # 价格不变
                current_trend = 0
                
            # 限制趋势持续性的最大绝对值
            current_trend = max(-max_trend_value, min(max_trend_value, current_trend))
            
            # 归一化到 -1 到 1 的范围
            normalized_trend = current_trend / max_trend_value
            trend_persistence.append(normalized_trend)
        
        # 添加第一天
        trend_persistence = [0] + trend_persistence
        
        return trend_strength, trend_persistence
    
    def _calculate_volume_price_confirmation(self, kLineData):
        """
        计算价格和交易量的确认关系
        
        Returns:
            list: 价格-交易量确认因子列表
        """
        if len(kLineData) < 2:
            return [0] * len(kLineData)
            
        factors = [0]  # 第一个点没有前一天数据
        
        for i in range(1, len(kLineData)):
            price_change = kLineData[i]['close'] - kLineData[i-1]['close']
            volume_change = kLineData[i]['volume'] - kLineData[i-1]['volume']
            
            # 价格上涨且成交量增加是强烈的做多信号 (+1.0)
            if price_change > 0 and volume_change > 0:
                factors.append(1.0)
            # 价格上涨但成交量减少是弱做多信号 (+0.3)
            elif price_change > 0 and volume_change <= 0:
                factors.append(0.3)
            # 价格下跌且成交量增加是强烈的做空信号 (-1.0)
            elif price_change < 0 and volume_change > 0:
                factors.append(-1.0)
            # 价格下跌但成交量减少是弱做空信号 (-0.3)
            else:
                factors.append(-0.3)
        
        return factors
    
    def _calculate_enhanced_strategy_factor(self, data_point: dict):
        """
        增强的策略影响因子计算
        
        Args:
            data_point: 包含策略买卖信号的数据点
            
        Returns:
            float: 增强的策略影响因子 (-1 到 1 之间)
        """
        buy_signals = data_point['strategy_buy']
        sell_signals = data_point['strategy_sell']
        total_signals = buy_signals + sell_signals
        
        if total_signals == 0:
            return 0
            
        # 如果买卖信号都存在，计算净信号比率
        if buy_signals > 0 and sell_signals > 0:
            # 买卖信号同时存在时，按比例计算
            net_signal = (buy_signals - sell_signals) / total_signals
            # 减弱混合信号的强度
            return net_signal * 0.5
            
        # 只有买入信号
        elif buy_signals > 0:
            # 信号强度随买入信号数量增加而增加，但有上限
            return min(1.0, buy_signals / 3)
            
        # 只有卖出信号
        elif sell_signals > 0:
            # 信号强度随卖出信号数量增加而增加，但有上限
            return max(-1.0, -sell_signals / 3)
            
        return 0
