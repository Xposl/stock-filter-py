"""
回测比较测试脚本 - 比较简化模式与高级模式的回测结果
"""
import sys
import os

# 将项目根目录添加到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.data_source_helper import DataSourceHelper
from core.strategy.cci_macd_strategy import CCIMacdStrategy
from core.strategy.cci_wma_strategy import CCIWmaStrategy
from core.strategy.art_dl_strategy import ArtDLStrategy
from core.analysis.strategy_evaluator import StrategyEvaluator
from core.handler.ticker_strategy_handler import StrategyCalculator
from core.strategy.volume_supertrend_ai_strategy import VolumeSuperTrendAIStrategy

def load_test_data(ticker_code):
    """加载测试用的K线数据
    
    Args:
        ticker_code: 股票代码
    
    Returns:
        list: K线数据列表
    """
    # 这里使用TickerKLineHandler加载数据，您可能需要根据实际情况调整
    try:
        kl_data = DataSourceHelper().get_kline_data(ticker_code)
        print(f"成功加载{ticker_code}的K线数据，共{len(kl_data)}条记录")
        return kl_data
    except Exception as e:
        print(f"加载K线数据失败: {e}")
        return []

def compare_backtest_results(ticker_code, strategy_class):
    """比较简化模式与高级模式的回测结果
    
    Args:
        ticker_code: 股票代码
    """
    # 加载K线数据
    kl_data = load_test_data(ticker_code)
    if not kl_data:
        print("无法获取K线数据，测试终止")
        return
    
    # 创建策略对象
    strategy = strategy_class()
    
    # 1. 使用StrategyCalculator进行回测（原始方式）
    print("\n=== 使用原始StrategyCalculator进行回测 ===")
    calculator = StrategyCalculator([strategy])
    original_result = calculator.calculate_by_key(strategy.get_key(), kl_data)
    
    print(f"总交易次数: {original_result['trades']}")
    print(f"盈利交易: {original_result['win_trades']}")
    print(f"亏损交易: {original_result['loss_trades']}")
    print(f"胜率: {original_result['profitable']}%")
    print(f"净利润: {original_result['net_profit']}")
    print(f"净利润率: {original_result['net_profit_pre']}%")
    print(f"最终状态: {'做多' if original_result['status'] == 1 else '做空' if original_result['status'] == -1 else '空仓'}")
    
    # 2. 使用AdvancedBacktestEngine的简化模式进行回测
    print("\n=== 使用AdvancedBacktestEngine的简化模式进行回测 ===")
    evaluator = StrategyEvaluator()
    simple_evaluation = evaluator.evaluate_strategy(strategy, kl_data, simple_mode=True)
    simple_result = simple_evaluation['backtest_result']
    
    print(f"总交易次数: {simple_result['metrics']['summary']['total_trades']}")
    print(f"盈利交易: {simple_result['metrics']['summary']['winning_trades']}")
    print(f"亏损交易: {simple_result['metrics']['summary']['losing_trades']}")
    print(f"胜率: {simple_result['metrics']['summary']['win_rate'] * 100:.2f}%")
    print(f"净利润: {simple_result['metrics']['returns']['total_profit']:.2f}")
    print(f"净利润率: {simple_result['metrics']['returns']['profit_pct'] * 100:.2f}%")
    print(f"最终资产: {simple_result['equity_curve'][-1]['total_value']:.2f}")
    
    # 3. 使用AdvancedBacktestEngine的高级模式进行回测
    print("\n=== 使用AdvancedBacktestEngine的高级模式进行回测 ===")
    # 将仓位管理从默认的20%改为80%
    evaluator.backtest_engine.max_position_pct = 0.5
    advanced_evaluation = evaluator.evaluate_strategy(strategy, kl_data, simple_mode=False)
    advanced_result = advanced_evaluation['backtest_result']
    
    print(f"总交易次数: {advanced_result['metrics']['summary']['total_trades']}")
    print(f"盈利交易: {advanced_result['metrics']['summary']['winning_trades']}")
    print(f"亏损交易: {advanced_result['metrics']['summary']['losing_trades']}")
    print(f"胜率: {advanced_result['metrics']['summary']['win_rate'] * 100:.2f}%")
    print(f"净利润: {advanced_result['metrics']['returns']['total_profit']:.2f}")
    print(f"净利润率: {advanced_result['metrics']['returns']['profit_pct'] * 100:.2f}%")
    print(f"最终资产: {advanced_result['equity_curve'][-1]['total_value']:.2f}")
    
    # 调试信息 - 检查高级模式的资产变化
    print("\n资产变化详情:")
    print(f"初始资金: {evaluator.backtest_engine.initial_capital}")
    print(f"最终资本: {advanced_result['equity_curve'][-1]['capital']:.2f}")
    print(f"最终持仓价值: {advanced_result['equity_curve'][-1]['holding_value']:.2f}")
    
    # 显示交易成本
    print(f"手续费总计: {advanced_result['costs']['total_commission']:.2f}")
    print(f"滑点成本总计: {advanced_result['costs']['total_slippage']:.2f}")
    
    # 显示所有交易明细
    print("\n交易明细:")
    for i, trade in enumerate(advanced_result['trades']):
        print(f"交易 {i+1}:")
        print(f"  开始时间: {trade['entry_date']}")
        print(f"  结束时间: {trade['exit_date']}")
        print(f"  类型: {trade['close_type']}")
        print(f"  方向: {'做多' if trade['direction'] == 1 else '做空'}")
        print(f"  买入价: {trade['entry_price']:.2f}, 卖出价: {trade['exit_price']:.2f}")
        print(f"  数量: {trade['size']}")
        print(f"  收益: {trade['profit']:.2f} ({trade['profit_pct'] * 100:.2f}%)")
        print(f"  交易成本: {trade['commission'] + trade['slippage']:.2f}")
    
    # 比较结果差异
    print("\n=== 结果比较 ===")
    print("简化模式 vs 高级模式:")
    trades_diff = simple_result['metrics']['summary']['total_trades'] - advanced_result['metrics']['summary']['total_trades']
    print(f"交易次数差异: {trades_diff} ({'+' if trades_diff > 0 else ''}{trades_diff / max(1, advanced_result['metrics']['summary']['total_trades']) * 100:.2f}%)")
    
    winrate_diff = simple_result['metrics']['summary']['win_rate'] - advanced_result['metrics']['summary']['win_rate']
    print(f"胜率差异: {winrate_diff * 100:.2f}% ({'+' if winrate_diff > 0 else ''}{winrate_diff / max(0.01, advanced_result['metrics']['summary']['win_rate']) * 100:.2f}%)")
    
    profit_diff = simple_result['metrics']['returns']['total_profit'] - advanced_result['metrics']['returns']['total_profit']
    print(f"利润差异: {profit_diff:.2f} ({'+' if profit_diff > 0 else ''}{profit_diff / max(1, abs(advanced_result['metrics']['returns']['total_profit'])) * 100:.2f}%)")
    
    asset_diff = simple_result['equity_curve'][-1]['total_value'] - advanced_result['equity_curve'][-1]['total_value']
    print(f"最终资产差异: {asset_diff:.2f} ({'+' if asset_diff > 0 else ''}{asset_diff / max(1, advanced_result['equity_curve'][-1]['total_value']) * 100:.2f}%)")
    
    print("\n高级模式额外信息:")
    print(f"最大回撤: {advanced_result['metrics']['risk']['max_drawdown'] * 100:.2f}%")
    print(f"年化收益: {advanced_result['metrics']['returns']['annual_return'] * 100:.2f}%")
    print(f"夏普比率: {advanced_result['metrics']['risk']['sharpe_ratio']:.2f}")
    print(f"索提诺比率: {advanced_result['metrics']['risk']['sortino_ratio']:.2f}")
    print(f"交易成本: {advanced_result['costs']['total_commission'] + advanced_result['costs']['total_slippage']:.2f}")

if __name__ == "__main__":
    # 可以使用您的实际股票代码替换
    ticker_code = "SZ.300840"  # 示例代码
    compare_backtest_results(ticker_code, VolumeSuperTrendAIStrategy)
