import numpy as np
import pandas as pd
from datetime import datetime
from enum import Enum

class PositionSizing(Enum):
    FIXED = 'fixed'           # 固定金额
    PERCENT = 'percent'       # 资金百分比
    KELLY = 'kelly'          # 凯利公式
    VOLATILITY = 'volatility' # 波动率调整
    PYRAMID = 'pyramid'       # 金字塔加仓

class StopLossType(Enum):
    FIXED = 'fixed'           # 固定止损
    TRAILING = 'trailing'     # 跟踪止损
    ATR = 'atr'              # ATR止损
    TIME = 'time'            # 时间止损
    COMPOSITE = 'composite'   # 复合止损

class AdvancedBacktestEngine:
    """增强的回测引擎，提供更灵活的交易模拟和风险管理"""
    
    def __init__(self, initial_capital=100000, position_sizing='fixed', 
                 max_position_pct=0.2, stop_loss_pct=0.05, trailing_stop_pct=None,
                 slippage_pct=0.001, commission_pct=0.0003, atr_period=14,
                 pyramid_factor=0.5, max_pyramid_levels=3, time_stop_days=10):
        """
        初始化回测引擎
        
        参数:
        initial_capital: 初始资金
        position_sizing: 仓位管理策略
        max_position_pct: 单笔最大仓位占比
        stop_loss_pct: 止损百分比
        trailing_stop_pct: 跟踪止损百分比
        slippage_pct: 滑点百分比
        commission_pct: 手续费率
        atr_period: ATR计算周期
        pyramid_factor: 金字塔加仓因子
        max_pyramid_levels: 最大金字塔加仓级数
        time_stop_days: 时间止损天数
        """
        self.initial_capital = initial_capital
        self.position_sizing = PositionSizing(position_sizing)
        self.max_position_pct = max_position_pct
        self.stop_loss_pct = stop_loss_pct
        self.trailing_stop_pct = trailing_stop_pct
        self.slippage_pct = slippage_pct
        self.commission_pct = commission_pct
        self.atr_period = atr_period
        self.pyramid_factor = pyramid_factor
        self.max_pyramid_levels = max_pyramid_levels
        self.time_stop_days = time_stop_days
        
        # 交易成本统计
        self.total_slippage = 0
        self.total_commission = 0
        self.transaction_costs = []
        
    def run_backtest(self, strategy_obj, kl_data):
        """运行回测"""
        # 初始化结果数据结构
        result = {
            'equity_curve': [],  # 资金曲线
            'positions': [],     # 持仓记录
            'trades': [],        # 交易记录
            'metrics': {},       # 绩效指标
            'pos_data': [],      # 策略信号
            'costs': {}          # 交易成本分析
        }
        
        # 获取策略生成的信号
        pos_data = strategy_obj.calculate(kl_data)
        result['pos_data'] = pos_data
        length = len(kl_data)
        
        # 计算ATR
        df = pd.DataFrame(kl_data)
        df['tr'] = self._calculate_tr(df)
        df['atr'] = df['tr'].rolling(window=self.atr_period).mean()
        
        # 初始化交易状态
        current_capital = self.initial_capital  # 当前资金
        holdings = 0  # 当前持仓数量
        current_position = None  # 当前持仓信息
        highest_price = 0  # 用于跟踪止损
        pyramid_level = 0  # 当前金字塔加仓级数
        
        # 记录每日资金曲线
        for i in range(length):
            day_data = kl_data[i]
            
            # 行情数据
            open_price = day_data['open']
            high_price = day_data['high']
            low_price = day_data['low']
            close_price = day_data['close']
            date = day_data['time_key']
            current_atr = df.iloc[i]['atr'] if not pd.isna(df.iloc[i]['atr']) else 0
            
            # 当日交易信号
            current_signal = pos_data[i]
            prev_signal = pos_data[i-1] if i > 0 else 0
            
            # 检查是否满足时间止损条件
            if current_position and self.time_stop_days:
                days_in_trade = (pd.to_datetime(date) - pd.to_datetime(current_position['entry_date'])).days
                if days_in_trade >= self.time_stop_days:
                    # 执行时间止损
                    self._close_position(result, current_position, holdings, open_price, date, 'time_stop')
                    current_position = None
                    holdings = 0
                    highest_price = 0
                    pyramid_level = 0
            
            # 当信号变化时进行交易
            if current_signal != prev_signal:
                # 有持仓且信号发生反转或变为中性，则平仓
                if holdings != 0 and (current_signal == 0 or current_signal == -prev_signal):
                    self._close_position(result, current_position, holdings, open_price, date)
                    current_position = None
                    holdings = 0
                    highest_price = 0
                    pyramid_level = 0
                
                # 开新仓位
                if current_signal != 0 and (current_position is None or current_signal != current_position['direction']):
                    # 计算仓位大小
                    position_size = self._calculate_position_size(
                        current_capital, open_price, current_signal, current_atr
                    )
                    
                    if position_size > 0:
                        new_position = self._open_position(
                            position_size, open_price, current_signal, date, current_atr
                        )
                        if new_position:
                            current_position = new_position
                            holdings = new_position['size']
                            highest_price = open_price
                            pyramid_level = 1
            
            # 金字塔加仓检查
            elif (current_position and 
                  current_signal == current_position['direction'] and 
                  pyramid_level < self.max_pyramid_levels and 
                  self.position_sizing == PositionSizing.PYRAMID):
                # 计算是否满足加仓条件
                if self._check_pyramid_conditions(current_position, close_price, current_atr):
                    # 计算加仓大小
                    pyramid_size = self._calculate_pyramid_size(
                        current_capital, close_price, current_signal, pyramid_level
                    )
                    if pyramid_size > 0:
                        pyramid_position = self._open_position(
                            pyramid_size, close_price, current_signal, date, current_atr
                        )
                        if pyramid_position:
                            holdings += pyramid_position['size']
                            pyramid_level += 1
            
            # 更新止损价格
            if current_position:
                stop_price = self._calculate_stop_loss(
                    current_position, high_price, low_price, current_atr, 
                    StopLossType.COMPOSITE
                )
                
                # 检查是否触发止损
                if ((current_position['direction'] == 1 and low_price <= stop_price) or
                    (current_position['direction'] == -1 and high_price >= stop_price)):
                    # 执行止损
                    self._close_position(result, current_position, holdings, stop_price, date, 'stop_loss')
                    current_position = None
                    holdings = 0
                    highest_price = 0
                    pyramid_level = 0
                else:
                    # 更新跟踪止损价格
                    highest_price = max(highest_price, high_price) if current_position['direction'] == 1 else min(highest_price, low_price)
            
            # 计算当日总资产价值
            portfolio_value = current_capital
            if holdings != 0:
                portfolio_value += close_price * holdings
            
            # 记录资金曲线
            equity_point = {
                'date': date,
                'capital': current_capital,
                'holdings': holdings,
                'holding_value': close_price * holdings if holdings != 0 else 0,
                'total_value': portfolio_value,
                'pyramid_level': pyramid_level
            }
            result['equity_curve'].append(equity_point)
        
        # 计算绩效指标
        result['metrics'] = self._calculate_performance_metrics(result)
        
        # 汇总交易成本
        result['costs'] = {
            'total_slippage': self.total_slippage,
            'total_commission': self.total_commission,
            'cost_analysis': self._analyze_transaction_costs()
        }
        
        return result
    
    def _calculate_tr(self, df):
        """计算真实波幅TR"""
        high = df['high']
        low = df['low']
        close = df['close']
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr
    
    def _calculate_position_size(self, capital, price, direction, atr):
        """计算仓位大小"""
        if self.position_sizing == PositionSizing.FIXED:
            return min(capital, self.initial_capital * self.max_position_pct)
        
        elif self.position_sizing == PositionSizing.PERCENT:
            return capital * self.max_position_pct
        
        elif self.position_sizing == PositionSizing.KELLY:
            # 使用历史交易数据计算凯利仓位
            win_rate = 0.55  # 假设胜率
            win_loss_ratio = 1.5  # 假设盈亏比
            kelly_pct = win_rate - ((1 - win_rate) / win_loss_ratio)
            kelly_pct = max(0, min(kelly_pct, self.max_position_pct))
            return capital * kelly_pct
        
        elif self.position_sizing == PositionSizing.VOLATILITY:
            # 基于ATR的波动率调整仓位
            if atr > 0:
                volatility_factor = 1 / (atr / price)
                position_pct = min(self.max_position_pct * volatility_factor, self.max_position_pct)
                return capital * position_pct
            return capital * self.max_position_pct
        
        elif self.position_sizing == PositionSizing.PYRAMID:
            return capital * self.max_position_pct
        
        return capital * self.max_position_pct
    
    def _calculate_pyramid_size(self, capital, price, direction, level):
        """计算金字塔加仓大小"""
        base_size = capital * self.max_position_pct
        return base_size * (self.pyramid_factor ** level)
    
    def _check_pyramid_conditions(self, position, current_price, current_atr):
        """检查是否满足金字塔加仓条件"""
        if position['direction'] == 1:
            return current_price > position['entry_price'] + current_atr
        else:
            return current_price < position['entry_price'] - current_atr
    
    def _calculate_stop_loss(self, position, high_price, low_price, atr, stop_type=StopLossType.FIXED):
        """计算止损价格"""
        if stop_type == StopLossType.FIXED:
            return position['entry_price'] * (1 - self.stop_loss_pct * position['direction'])
        
        elif stop_type == StopLossType.TRAILING:
            if position['direction'] == 1:
                return high_price * (1 - self.trailing_stop_pct)
            else:
                return low_price * (1 + self.trailing_stop_pct)
        
        elif stop_type == StopLossType.ATR:
            return position['entry_price'] - (atr * 2 * position['direction'])
        
        elif stop_type == StopLossType.COMPOSITE:
            # 综合考虑多个止损条件
            fixed_stop = position['entry_price'] * (1 - self.stop_loss_pct * position['direction'])
            trailing_stop = high_price * (1 - self.trailing_stop_pct) if position['direction'] == 1 else low_price * (1 + self.trailing_stop_pct)
            atr_stop = position['entry_price'] - (atr * 2 * position['direction'])
            
            if position['direction'] == 1:
                return max(fixed_stop, trailing_stop, atr_stop)
            else:
                return min(fixed_stop, trailing_stop, atr_stop)
        
        return position['entry_price'] * (1 - self.stop_loss_pct * position['direction'])
    
    def _open_position(self, position_size, price, direction, date, atr):
        """开仓"""
        # 计算开仓价格（考虑滑点）
        entry_price = self._apply_slippage(price, direction)
        
        # 计算可买入数量
        max_shares = int(position_size / entry_price)
        if max_shares <= 0:
            return None
            
        # 计算交易成本
        commission = entry_price * max_shares * self.commission_pct
        slippage = abs(entry_price - price) * max_shares
        
        self.total_commission += commission
        self.total_slippage += slippage
        
        self.transaction_costs.append({
            'date': date,
            'type': 'open',
            'price': entry_price,
            'size': max_shares,
            'commission': commission,
            'slippage': slippage
        })
        
        return {
            'entry_date': date,
            'entry_price': entry_price,
            'direction': direction,
            'size': max_shares,
            'stop_loss': self._calculate_stop_loss({'entry_price': entry_price, 'direction': direction}, price, price, atr),
            'commission': commission,
            'slippage': slippage
        }
    
    def _close_position(self, result, position, holdings, price, date, close_type='normal'):
        """平仓"""
        # 计算平仓价格（考虑滑点）
        exit_price = self._apply_slippage(price, -position['direction'])
        
        # 计算收益
        profit = (exit_price - position['entry_price']) * holdings * position['direction']
        
        # 计算交易成本
        commission = exit_price * holdings * self.commission_pct
        slippage = abs(exit_price - price) * holdings
        
        self.total_commission += commission
        self.total_slippage += slippage
        
        self.transaction_costs.append({
            'date': date,
            'type': 'close',
            'price': exit_price,
            'size': holdings,
            'commission': commission,
            'slippage': slippage
        })
        
        # 记录交易
        trade = {
            'entry_date': position['entry_date'],
            'entry_price': position['entry_price'],
            'exit_date': date,
            'exit_price': exit_price,
            'direction': position['direction'],
            'size': holdings,
            'profit': profit - commission - slippage,
            'profit_pct': (profit - commission - slippage) / (position['entry_price'] * holdings),
            'commission': commission,
            'slippage': slippage,
            'close_type': close_type
        }
        result['trades'].append(trade)
    
    def _apply_slippage(self, price, direction):
        """应用滑点模型"""
        return price * (1 + self.slippage_pct * direction)
    
    def _analyze_transaction_costs(self):
        """分析交易成本"""
        if not self.transaction_costs:
            return {}
        
        df = pd.DataFrame(self.transaction_costs)
        
        return {
            'cost_summary': {
                'total_commission': self.total_commission,
                'total_slippage': self.total_slippage,
                'total_cost': self.total_commission + self.total_slippage,
                'avg_commission_per_trade': self.total_commission / len(df),
                'avg_slippage_per_trade': self.total_slippage / len(df)
            },
            'cost_by_type': df.groupby('type')[['commission', 'slippage']].sum().to_dict(),
            'cost_distribution': {
                'commission_pct': self.total_commission / (self.total_commission + self.total_slippage),
                'slippage_pct': self.total_slippage / (self.total_commission + self.total_slippage)
            }
        }
    
    def _calculate_performance_metrics(self, result):
        """计算绩效指标"""
        trades = result['trades']
        equity_curve = [point['total_value'] for point in result['equity_curve']]
        
        # 基础指标
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['profit'] > 0])
        losing_trades = total_trades - winning_trades
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # 收益指标
        total_profit = sum(t['profit'] for t in trades)
        gross_profit = sum(t['profit'] for t in trades if t['profit'] > 0)
        gross_loss = sum(t['profit'] for t in trades if t['profit'] <= 0)
        
        profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else float('inf')
        
        # 回撤指标
        max_drawdown = 0
        peak = equity_curve[0]
        underwater_periods = []
        current_underwater = 0
        
        for value in equity_curve:
            if value > peak:
                peak = value
                if current_underwater > 0:
                    underwater_periods.append(current_underwater)
                current_underwater = 0
            else:
                drawdown = (peak - value) / peak
                max_drawdown = max(max_drawdown, drawdown)
                current_underwater += 1
        
        if current_underwater > 0:
            underwater_periods.append(current_underwater)
        
        # 计算年化收益率和风险调整收益
        total_return = (equity_curve[-1] - equity_curve[0]) / equity_curve[0]
        trading_days = len(equity_curve)
        annual_return = (1 + total_return) ** (252 / trading_days) - 1
        
        # 计算日收益率序列
        daily_returns = []
        for i in range(1, len(equity_curve)):
            daily_return = (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1]
            daily_returns.append(daily_return)
        
        daily_returns = np.array(daily_returns)
        volatility = np.std(daily_returns) * np.sqrt(252)
        
        # 计算风险指标
        sharpe_ratio = np.sqrt(252) * np.mean(daily_returns) / np.std(daily_returns) if len(daily_returns) > 0 and np.std(daily_returns) > 0 else 0
        sortino_ratio = np.sqrt(252) * np.mean(daily_returns) / np.std(daily_returns[daily_returns < 0]) if len(daily_returns[daily_returns < 0]) > 0 else 0
        
        # 计算交易统计
        avg_trade_duration = np.mean([
            (pd.to_datetime(t['exit_date']) - pd.to_datetime(t['entry_date'])).days 
            for t in trades
        ])
        
        profit_loss_ratio = abs(np.mean([t['profit'] for t in trades if t['profit'] > 0])) / abs(np.mean([t['profit'] for t in trades if t['profit'] < 0])) if losing_trades > 0 else float('inf')
        
        return {
            'summary': {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'avg_trade_duration': avg_trade_duration,
                'profit_loss_ratio': profit_loss_ratio
            },
            'returns': {
                'total_profit': total_profit,
                'profit_pct': total_profit / self.initial_capital,
                'gross_profit': gross_profit,
                'gross_loss': gross_loss,
                'profit_factor': profit_factor,
                'annual_return': annual_return
            },
            'risk': {
                'max_drawdown': max_drawdown,
                'avg_drawdown': np.mean([dd/peak for dd in underwater_periods]) if underwater_periods else 0,
                'max_drawdown_duration': max(underwater_periods) if underwater_periods else 0,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'sortino_ratio': sortino_ratio
            },
            'efficiency': {
                'profit_per_trade': total_profit / total_trades if total_trades > 0 else 0,
                'avg_win': gross_profit / winning_trades if winning_trades > 0 else 0,
                'avg_loss': gross_loss / losing_trades if losing_trades > 0 else 0,
                'largest_win': max([t['profit'] for t in trades]) if trades else 0,
                'largest_loss': min([t['profit'] for t in trades]) if trades else 0
            }
        }
