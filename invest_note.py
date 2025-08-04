#coding=UTF-8
import os
import sys

import matplotlib

from core.analysis.advanced_backtest_engine import AdvancedBacktestEngine
from core.analysis.strategy_evaluator import StrategyEvaluator
from core.data_source_helper import DataSourceHelper
from core.strategy import DEFAULT_STRATEGIES

from app.handlers.ticker_handler import TickerHandler

# 配置matplotlib字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'Microsoft YaHei', 'STHeiti', 'Heiti TC']
matplotlib.rcParams['axes.unicode_minus'] = False


def print_header():
    """打印程序标题"""
    print("=" * 50)
    print("                 InvestNote                  ")
    print("             投资分析工具 v1.0                ")
    print("=" * 50)

def print_main_menu():
    """打印主菜单"""
    print("\n请选择要执行的操作：")
    print("1. 更新股票列表")
    print("2. 分析股票")
    print("3. 分时分析股票")
    print("4. 批量更新股票数据")
    print("5. 策略分析")
    print("0. 退出程序")
    print("-" * 50)

def get_ticker_code():
    """获取股票代码"""
    print("\n请选择股票市场：")
    print("1. 中国股市 (zh)")
    print("2. 香港股市 (hk)")
    print("3. 美国股市 (us)")

    market_choice = input("请输入选择 (1-3): ")

    if market_choice == "1":
        market = "zh"
    elif market_choice == "2":
        market = "hk"
    elif market_choice == "3":
        market = "us"
    else:
        print("无效选择，默认使用中国股市")
        market = "zh"

    ticker_code = input(f"请输入{market}股票代码: ")

    code = None
    if market == "hk":
        code = f"HK.{ticker_code.zfill(5)}"
    elif market == "zh":
        code = ticker_code.zfill(6)
        if code.startswith('0') or code.startswith('3'):
            code = f"SZ.{code}"
        elif code.startswith('6') or code.startswith('7') or code.startswith('9'):
            code = f"SH.{code}"
    elif market == "us":
        code = f"US.{ticker_code}"

    return code

def analyze_strategies(code, days=250):
    """分析股票的多个策略表现"""
    dataSource = DataSourceHelper()

    # 获取K线数据
    kl_data = dataSource.get_kline_data(code, days)
    if kl_data is None or len(kl_data) == 0:
        print(f"无法获取股票 {code} 的K线数据")
        return

    # 初始化策略评估器
    evaluator = StrategyEvaluator()
    # 设置回测引擎参数，包括跟踪止损等风险管理参数
    evaluator.backtest_engine = AdvancedBacktestEngine(
        initial_capital=100000,
        position_sizing='fixed',
        max_position_pct=1,
        stop_loss_pct=0.05,
        trailing_stop_pct=0.05,  # 添加跟踪止损参数
        slippage_pct=0.001,
        commission_pct=0.0003
    )

    # 准备策略列表
    strategies = DEFAULT_STRATEGIES

    print(f"\n开始分析股票 {code} 的策略表现...")
    print("-" * 50)

    # 评估所有策略
    results = evaluator.evaluate_strategies(strategies, kl_data)

    # 打印评估结果
    for strategy_name, result in results.items():
        print(f"\n策略: {strategy_name}")
        metrics = result['backtest_result']['metrics']
        trades = result['backtest_result']['trades']

        # 打印策略总体表现
        print("\n策略总体表现:")
        print(f"总评分: {result['rating']['total_score']:.2f}")
        print(f"评级: {result['rating']['rating']}")
        print(f"交易次数: {len(trades)}")
        print(f"胜率: {metrics['win_rate']:.2%}")
        print(f"年化收益: {metrics['annual_return']:.2%}")
        print(f"最大回撤: {metrics['max_drawdown']:.2%}")
        print(f"夏普比率: {metrics['sharpe_ratio']:.2f}")
        print(f"索提诺比率: {metrics['sortino_ratio']:.2f}")
        print(f"波动率: {metrics['volatility']:.2%}")

        # 打印市场环境分析
        if 'bull' in result['regime_analysis'] and 'bear' in result['regime_analysis']:
            print("\n市场环境分析:")
            print(f"牛市胜率: {result['regime_analysis']['bull']['win_rate']:.2%}")
            print(f"熊市胜率: {result['regime_analysis']['bear']['win_rate']:.2%}")

        # 计算总收益和收益率
        total_profit = sum(trade['profit'] for trade in trades)
        initial_capital = evaluator.backtest_engine.initial_capital
        total_return = total_profit / initial_capital if initial_capital > 0 else 0

        # 打印交易详情
        print("\n交易记录:")
        print("序号  操作      时间          价格      数量      收益")
        print("-" * 60)
        for i, trade in enumerate(trades, 1):
            entry_date = trade['entry_date'].strftime('%Y-%m-%d') if hasattr(trade['entry_date'], 'strftime') else str(trade['entry_date'])
            exit_date = trade['exit_date'].strftime('%Y-%m-%d') if hasattr(trade['exit_date'], 'strftime') else str(trade['exit_date'])
            direction = "买入" if trade['direction'] == 1 else "卖空"
            print(f"{i:2d}. {direction:6} {entry_date:10} {trade['entry_price']:9.3f} {trade['size']:8d}")
            print(f"    {'平仓':6} {exit_date:10} {trade['exit_price']:9.3f} {trade['size']:8d} {trade['profit']:9.2f}")

        print("-" * 60)
        print(f"总收益: {total_profit:,.2f}")
        print(f"收益率: {total_return:.2%}")
        print("-" * 60)

        # 检查是否有未平仓交易
        last_equity_point = result['backtest_result']['equity_curve'][-1]
        if last_equity_point['holdings'] != 0:
            print("\n注意: 存在未平仓交易!")
            print(f"持有方向: {'多头' if last_equity_point.get('pyramid_level', 0) > 0 and last_equity_point.get('holding_value', 0) > 0 else '空头'}")
            print(f"持仓数量: {last_equity_point['holdings']}")
            print(f"持仓价值: {last_equity_point['holding_value']}")
            print(f"持仓时间: {last_equity_point['entry_date'].strftime('%Y-%m-%d')}")
            print("-" * 60)

def update_batch_tickers():
    """批量更新股票数据菜单"""
    print("\n请选择批量更新方式：")
    print("1. 更新所有股票数据")
    print("2. 更新指定前缀的股票数据")
    print("0. 返回主菜单")

    choice = input("请输入选择 (0-2): ")

    dataSource = DataSourceHelper()

    if choice == "1":
        print("\n开始更新所有股票数据...")
        dataSource.update_all_tickers()
        print("更新完成")
    elif choice == "2":
        prefix = input("\n请输入股票代码前缀: ")
        print(f"\n开始更新以 {prefix} 开头的股票数据...")
        dataSource.update_tickers_start_with(prefix)
        print("更新完成")
    else:
        return

def run_interactive_mode():
    """运行交互式模式"""
    print_header()

    while True:
        print_main_menu()
        choice = input("请输入选择 (0-6): ")

        dataSource = DataSourceHelper()

        if choice == "0":
            print("谢谢使用，再见！")
            break

        elif choice == "1":
            print("\n开始更新股票列表...")
            TickerHandler().sync_tickers()
            print("股票列表更新完成")

        elif choice == "2":
            code = get_ticker_code()
            if code:
                print(f"\n开始分析股票 {code}...")
                days = input("请输入分析的天数 (默认250天): ")
                try:
                    days = int(days) if days.strip() else 250
                except ValueError:
                    days = 250
                dataSource.analysis_ticker(code, days)
                print(f"股票 {code} 分析完成")
            else:
                print("无效的股票代码")

        elif choice == "3":
            code = get_ticker_code()
            if code:
                print(f"\n开始分时分析股票 {code}...")
                days = input("请输入分析的天数 (默认400天): ")
                try:
                    days = int(days) if days.strip() else 400
                except ValueError:
                    days = 400
                dataSource.analysis_ticker_on_time(code, days)
                print(f"股票 {code} 分时分析完成")
            else:
                print("无效的股票代码")

        elif choice == "4":
            update_batch_tickers()

        elif choice == "5":
            code = get_ticker_code()
            if code:
                print(f"\n开始策略分析股票 {code}...")
                days = input("请输入分析的天数 (默认250天): ")
                try:
                    days = int(days) if days.strip() else 250
                except ValueError:
                    days = 250
                analyze_strategies(code, days)
            else:
                print("无效的股票代码")

        else:
            print("无效选择，请重新输入")

        input("\n按回车键继续...")

def run_command_line_mode():
    """运行命令行模式（保持原有功能）"""
    dataSource = DataSourceHelper()

    if sys.argv[1] == '-ticker':
        dataSource.update_ticker_list()

    elif sys.argv[1] == '-a':
        code = None
        if sys.argv[2] == 'hk':
            code = f'HK.{sys.argv[3].zfill(5)}'
        elif sys.argv[2] == 'zh':
            code = sys.argv[3].zfill(6)
            if code.startswith('0') or code.startswith('3'):
                code  = f'SZ.{code}'
            elif code.startswith('6') or code.startswith('7') or code.startswith('9'):
                code  = f'SH.{code}'
        elif sys.argv[2] == 'us':
            code = f'US.{sys.argv[3]}'

        if code is not None:
            days = 250
            if len(sys.argv) > 4:
                try:
                    days = int(sys.argv[4])
                except ValueError:
                    pass
            dataSource.analysis_ticker(code, days)

    elif sys.argv[1] == '-ao':
        code = None
        if sys.argv[2] == 'hk':
            code = f'HK.{sys.argv[3].zfill(5)}'
        elif sys.argv[2] == 'zh':
            code = sys.argv[3].zfill(6)
            if code.startswith('0') or code.startswith('3'):
                code  = f'SZ.{code}'
            elif code.startswith('6') or code.startswith('7') or code.startswith('9'):
                code  = f'SH.{code}'
        elif sys.argv[2] == 'us':
            code = f'US.{sys.argv[3]}'

        if code is not None:
            days = 400
            if len(sys.argv) > 4:
                try:
                    days = int(sys.argv[4])
                except ValueError:
                    pass
            dataSource.analysis_ticker_on_time(code, days)

    elif sys.argv[1] == '-all':
        dataSource.update_all_tickers()

    elif sys.argv[1] == '-prefix':
        if len(sys.argv) > 2:
            dataSource.update_tickers_start_with(sys.argv[2])
        else:
            print("错误：缺少前缀参数")

    elif sys.argv[1] == '-s':
        code = None
        if len(sys.argv) >= 4:
            if sys.argv[2] == 'hk':
                code = f'HK.{sys.argv[3].zfill(5)}'
            elif sys.argv[2] == 'zh':
                code = sys.argv[3].zfill(6)
                if code.startswith('0') or code.startswith('3'):
                    code = f'SZ.{code}'
                elif code.startswith('6') or code.startswith('7') or code.startswith('9'):
                    code = f'SH.{code}'
            elif sys.argv[2] == 'us':
                code = f'US.{sys.argv[3]}'

            if code is not None:
                days = 250
                if len(sys.argv) > 4:
                    try:
                        days = int(sys.argv[4])
                    except ValueError:
                        pass
                analyze_strategies(code, days)
            else:
                print("无效的股票代码")
        else:
            print("错误：缺少参数")
            print_help()

    elif sys.argv[1] == '-h' or sys.argv[1] == '--help':
        print_help()

    else:
        print("未知命令，请使用 -h 或 --help 查看帮助")

def print_help():
    """打印帮助信息"""
    print("InvestNote 使用帮助:")
    print("  无参数运行:            交互式菜单模式")
    print("  -ticker:              更新股票列表")
    print("  -a [市场] [代码] [天数]:  分析指定股票 (市场: zh/hk/us, 天数可选，默认250)")
    print("  -ao [市场] [代码] [天数]: 分时分析指定股票 (市场: zh/hk/us, 天数可选，默认400)")
    print("  -all:                 更新所有股票数据")
    print("  -prefix [前缀]:        更新指定前缀的股票数据")
    print("  -s [市场] [代码] [天数]:  策略分析股票 (市场: zh/hk/us, 天数可选，默认250)")
    print("  -hs, --high-score [阈值] [-e/--export] [-o/--output 文件路径]: 显示高评分股票")
    print("                        [阈值]: 评分阈值，可选，默认75")
    print("                        [-e/--export]: 导出到JSON，可选")
    print("                        [-o/--output]: 指定导出文件路径，可选")
    print("  -export-hs, --export-high-score [阈值] [-o/--output 文件路径]: 将高评分股票导出到JSON")
    print("                        [阈值]: 评分阈值，可选，默认75")
    print("                        [-o/--output]: 指定导出文件路径，可选")
    print("  -h, --help:           显示帮助信息")
    print("\n例子:")
    print("  python investNote.py               # 运行交互式菜单")
    print("  python investNote.py -ticker       # 更新股票列表")
    print("  python investNote.py -a zh 600000  # 分析上证股票600000")
    print("  python investNote.py -a hk 00700   # 分析港股00700")
    print("  python investNote.py -a us AAPL    # 分析美股AAPL")
    print("  python investNote.py -ao zh 600000 600  # 分时分析上证股票600000，数据范围600天")
    print("  python investNote.py -hs 80        # 显示评分大于等于80的股票")
    print("  python investNote.py -hs 80 -e     # 显示评分大于等于80的股票并导出到JSON")
    print("  python investNote.py -hs -e -o output/mystocks.json  # 导出评分大于等于75的股票到指定文件")
    print("  python investNote.py -export-hs 80  # 将评分大于等于80的股票直接导出到JSON")
    print("  python investNote.py -export-hs -o output/high_stocks.json  # 导出到指定文件")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # 无参数，进入交互式模式
        run_interactive_mode()
    else:
        # 有参数，使用命令行模式
        run_command_line_mode()
