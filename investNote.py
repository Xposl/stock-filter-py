#coding=UTF-8
import sys
from core.handler import DataSourceHelper
import datetime

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
        choice = input("请输入选择 (0-4): ")
        
        dataSource = DataSourceHelper()
        
        if choice == "0":
            print("谢谢使用，再见！")
            break
        
        elif choice == "1":
            print("\n开始更新股票列表...")
            dataSource.update_ticker_list()
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
            code = 'HK.%s'%sys.argv[3].zfill(5)
        elif sys.argv[2] == 'zh':
            code = sys.argv[3].zfill(6)
            if code.startswith('0') or code.startswith('3'):
                code  = 'SZ.%s'%code
            elif code.startswith('6') or code.startswith('7') or code.startswith('9'):
                code  = 'SH.%s'%code
        elif sys.argv[2] == 'us':
            code = 'US.%s'%sys.argv[3]

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
            code = 'HK.%s'%sys.argv[3].zfill(5)
        elif sys.argv[2] == 'zh':
            code = sys.argv[3].zfill(6)
            if code.startswith('0') or code.startswith('3'):
                code  = 'SZ.%s'%code
            elif code.startswith('6') or code.startswith('7') or code.startswith('9'):
                code  = 'SH.%s'%code
        elif sys.argv[2] == 'us':
            code = 'US.%s'%sys.argv[3]
        
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
    print("  -h, --help:           显示帮助信息")
    print("\n例子:")
    print("  python investNote.py               # 运行交互式菜单")
    print("  python investNote.py -ticker       # 更新股票列表")
    print("  python investNote.py -a zh 600000  # 分析上证股票600000")
    print("  python investNote.py -a hk 00700   # 分析港股00700")
    print("  python investNote.py -a us AAPL    # 分析美股AAPL")
    print("  python investNote.py -ao zh 600000 600  # 分时分析上证股票600000，数据范围600天")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # 无参数，进入交互式模式
        run_interactive_mode()
    else:
        # 有参数，使用命令行模式
        run_command_line_mode()
