import numpy as np
import pandas as pd
from core.analysis.advanced_backtest_engine import AdvancedBacktestEngine
from core.analysis.market_regime import MarketRegimeClassifier

class StrategyEvaluator:
    """策略综合评估器"""
    
    def __init__(self):
        self.backtest_engine = AdvancedBacktestEngine()
        self.regime_classifier = MarketRegimeClassifier()
    
    def evaluate_strategy(self, strategy_obj, kl_data, name=None):
        """全面评估单个策略"""
        # 运行回测
        backtest_result = self.backtest_engine.run_backtest(strategy_obj, kl_data)
        
        # 市场环境分析
        regime_analysis = self.regime_classifier.analyze_strategy_by_regime(
            backtest_result['trades'], kl_data
        )
        
        # 计算月度/季度/年度业绩
        period_performance = self._calculate_period_performance(backtest_result)
        
        # 计算风险指标
        risk_metrics = self._calculate_risk_metrics(backtest_result)
        
        # 补充基本指标
        if 'metrics' not in backtest_result:
            backtest_result['metrics'] = {}
        backtest_result['metrics'].update({
            'max_drawdown': risk_metrics['max_drawdown'],
            'win_rate': self._calculate_win_rate(backtest_result['trades']),
            'annual_return': self._calculate_annual_return(backtest_result['equity_curve']),
            'total_trades': len(backtest_result['trades']),
            'sharpe_ratio': risk_metrics['sharpe_ratio'],
            'volatility': risk_metrics['volatility'],
            'sortino_ratio': risk_metrics['sortino_ratio']
        })
        
        # 汇总评估报告
        evaluation = {
            'strategy_name': name or strategy_obj.get_key(),
            'backtest_result': backtest_result,
            'regime_analysis': regime_analysis,
            'period_performance': period_performance,
            'risk_metrics': risk_metrics,
            'rating': self._calculate_strategy_rating(backtest_result, regime_analysis)
        }
        
        return evaluation
    
    def evaluate_strategies(self, strategies, kl_data):
        """评估多个策略"""
        results = {}
        for strategy in strategies:
            key = strategy.get_key()
            results[key] = self.evaluate_strategy(strategy, kl_data, key)
        return results
    
    def _calculate_period_performance(self, backtest_result):
        """计算不同时间周期的绩效"""
        # 创建每日权益曲线的DataFrame
        equity_df = pd.DataFrame(backtest_result['equity_curve'])
        equity_df['date'] = pd.to_datetime(equity_df['date'])
        equity_df.set_index('date', inplace=True)
        
        # 计算每日收益率
        equity_df['daily_return'] = equity_df['total_value'].pct_change()
        
        # 月度绩效
        monthly_returns = equity_df['daily_return'].resample('ME').apply(
            lambda x: (1 + x).prod() - 1
        )
        
        # 季度绩效
        quarterly_returns = equity_df['daily_return'].resample('QE').apply(
            lambda x: (1 + x).prod() - 1
        )
        
        # 年度绩效
        yearly_returns = equity_df['daily_return'].resample('YE').apply(
            lambda x: (1 + x).prod() - 1
        )
        
        return {
            'monthly_returns': monthly_returns.to_dict(),
            'quarterly_returns': quarterly_returns.to_dict(),
            'yearly_returns': yearly_returns.to_dict(),
            'worst_month': monthly_returns.min(),
            'best_month': monthly_returns.max(),
            'worst_quarter': quarterly_returns.min(),
            'best_quarter': quarterly_returns.max(),
            'worst_year': yearly_returns.min(),
            'best_year': yearly_returns.max()
        }
    
    def _calculate_risk_metrics(self, backtest_result):
        """计算风险指标"""
        equity_curve = [point['total_value'] for point in backtest_result['equity_curve']]
        daily_returns = []
        
        # 计算每日收益率
        for i in range(1, len(equity_curve)):
            daily_return = (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1]
            daily_returns.append(daily_return)
        
        daily_returns = np.array(daily_returns)
        
        # 计算最大回撤
        max_drawdown = 0
        peak = equity_curve[0]
        for value in equity_curve:
            if value > peak:
                peak = value
            else:
                drawdown = (peak - value) / peak
                max_drawdown = max(max_drawdown, drawdown)
        
        # 计算波动率
        volatility = np.std(daily_returns) * np.sqrt(252) if len(daily_returns) > 0 else 0
        
        # 计算下行风险（负收益的标准差）
        downside_returns = daily_returns[daily_returns < 0]
        downside_risk = np.std(downside_returns) * np.sqrt(252) if len(downside_returns) > 0 else 0
        
        # 计算平均收益和风险调整收益
        mean_return = np.mean(daily_returns) if len(daily_returns) > 0 else 0
        risk_free_rate = 0.03  # 假设无风险利率为3%
        excess_returns = daily_returns - risk_free_rate/252
        
        # 计算夏普比率（如果没有足够的数据或波动率为0，则返回0）
        std_returns = np.std(daily_returns) if len(daily_returns) > 0 else 0
        sharpe_ratio = (np.mean(excess_returns) * 252) / (std_returns * np.sqrt(252)) if std_returns > 0 else 0
        
        # 计算索提诺比率（如果没有下行风险，则返回0）
        sortino_ratio = (mean_return * 252) / downside_risk if downside_risk > 0 else 0
        
        # 计算最大回撤持续时间
        underwater = []
        current_underwater = 0
        peak = equity_curve[0]
        
        for value in equity_curve:
            if value > peak:
                peak = value
                if current_underwater > 0:
                    underwater.append(current_underwater)
                current_underwater = 0
            else:
                current_underwater += 1
                
        if current_underwater > 0:
            underwater.append(current_underwater)
            
        max_drawdown_duration = max(underwater) if underwater else 0
        
        return {
            'volatility': volatility,
            'max_drawdown': max_drawdown,
            'downside_risk': downside_risk,
            'sortino_ratio': sortino_ratio,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown_duration': max_drawdown_duration
        }
    
    def _calculate_win_rate(self, trades):
        """计算策略胜率"""
        if not trades:
            return 0
        winning_trades = sum(1 for trade in trades if trade['profit'] > 0)
        return winning_trades / len(trades)
    
    def _calculate_annual_return(self, equity_curve):
        """计算年化收益率"""
        if not equity_curve or len(equity_curve) < 2:
            return 0
        start_value = equity_curve[0]['total_value']
        end_value = equity_curve[-1]['total_value']
        days = len(equity_curve)
        if start_value <= 0:
            return 0
        return (end_value / start_value) ** (252 / days) - 1
    
    def _calculate_strategy_rating(self, backtest_result, regime_analysis):
        """计算策略综合评分"""
        metrics = backtest_result['metrics']
        
        # 基础绩效 (40%)
        performance_score = min(10, metrics['annual_return'] * 10)
        
        # 风险控制 (30%)
        risk_score = 10 * (1 - metrics['max_drawdown'])
        
        # 稳定性 (30%)
        stability_factors = []
        
        # 在不同市场环境下的表现一致性
        if 'bull' in regime_analysis and 'bear' in regime_analysis:
            bull_win_rate = regime_analysis['bull']['win_rate']
            bear_win_rate = regime_analysis['bear']['win_rate']
            # 熊牛市都有不错的胜率
            consistency = min(bull_win_rate, bear_win_rate) / max(bull_win_rate, bear_win_rate) if max(bull_win_rate, bear_win_rate) > 0 else 0
            stability_factors.append(consistency)
        
        # 交易频率
        trade_frequency = min(1, metrics['total_trades'] / 250)
        stability_factors.append(trade_frequency)
        
        # 胜率
        stability_factors.append(metrics['win_rate'])
        
        stability_score = 10 * np.mean(stability_factors)
        
        # 综合评分 (满分100)
        total_score = 0.4 * performance_score + 0.3 * risk_score + 0.3 * stability_score
        
        return {
            'performance_score': performance_score,
            'risk_score': risk_score,
            'stability_score': stability_score,
            'total_score': total_score,
            'rating': self._convert_score_to_rating(total_score)
        }
    
    def _convert_score_to_rating(self, score):
        """将分数转换为评级"""
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B+'
        elif score >= 60:
            return 'B'
        elif score >= 50:
            return 'C+'
        elif score >= 40:
            return 'C'
        else:
            return 'D'
