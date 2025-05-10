import pandas as pd
from datetime import datetime, timedelta
import random
import numpy as np
import matplotlib.pyplot as plt

from core.strategy.cci_macd_strategy import CCIMacdStrategy
from core.strategy.cci_macd_strategy import CCIMacdStrategy
from core.strategy.art_dl_strategy import ArtDLStrategy
from core.analysis.advanced_backtest_engine import AdvancedBacktestEngine
from core.analysis.backtest_visualizer import BacktestVisualizer
from core.data_source_helper import DataSourceHelper
from core.strategy import DEFAULT_STRATEGIES


def load_real_data(file_path=None):
    """从文件加载实际的K线数据，如果文件不存在则返回None"""
    if file_path is None:
        return None
    
    try:
        df = pd.read_csv(file_path)
        kl_data = []
        
        for _, row in df.iterrows():
            kl_data.append({
                'time_key': row['date'],
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': row['volume'] if 'volume' in row else 0,
                'amount': row['amount'] if 'amount' in row else 0,
            })
        
        return kl_data
    except Exception as e:
        print(f"加载数据失败: {e}")
        return None

def run_example_backtest(strategy_class, kl_data, title=None):
    """运行示例回测并可视化结果"""
    # 创建策略实例
    strategy = strategy_class()
    
    # 创建回测引擎 (高级模式)
    backtest_engine = AdvancedBacktestEngine(
        initial_capital=100000,
        position_sizing='percent',
        max_position_pct=0.3,
        stop_loss_pct=0.05,
        trailing_stop_pct=0.08,
        slippage_pct=0.001
    )
    
    # 运行回测
    print(f"运行回测: {strategy.get_key()}")
    result = backtest_engine.run_backtest(strategy, kl_data)
    
    # 创建可视化实例
    visualizer = BacktestVisualizer()
    
    # 设置图表标题
    if title is None:
        title = f"{strategy.get_key()}策略回测"
    
    # 可视化回测结果 (K线图和买卖点)
    print("生成K线交易图...")
    visualizer.visualize_backtest(result, kl_data, title=title)
    
    # 可视化性能指标
    print("生成性能评估图...")
    visualizer.visualize_performance(result, title=f"{title} - 性能评估")
    
    # 可视化交易分析
    print("生成交易分析图...")
    visualizer.visualize_trades_analysis(result, title=f"{title} - 交易分析")
    
    return result

if __name__ == "__main__":
    # 1. 生成示例数据或加载真实数据
    ticker_code = "SZ.000006"  # 示例代码
    kl_data = DataSourceHelper().get_kline_data(ticker_code)
    # kl_data = load_real_data('path/to/your/data.csv')  # 可选：加载真实数据
    
    # 2. 单一策略回测示例
    print("\n=== 单一策略回测示例 ===")
    run_example_backtest(ArtDLStrategy, kl_data, title="均线交叉策略回测")
    
    print("\n回测可视化示例完成!")
