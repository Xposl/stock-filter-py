import akshare as ak
import pandas as pd

def get_last_trade_dates():
    """获取A股、港股、美股的最后交易日"""
    results = {}
    
    # A股最后交易日
    try:
        stock_sse_summary_df = ak.stock_sse_summary()
        report_time_row = stock_sse_summary_df[stock_sse_summary_df.iloc[:, 0] == "报告时间"]
        if not report_time_row.empty:
          # 获取"股票"列的值（第2列，索引为1）
          report_time_str = report_time_row.iloc[0, 1]
          # 格式化日期字符串
          formatted_date = f"{report_time_str[:4]}-{report_time_str[4:6]}-{report_time_str[6:]}"
          results["zh"] = formatted_date
    except Exception as e:
        results["zh"] = "获取失败"
            
    
    # 港股最后交易日
    try:
        hk_index_df = ak.stock_hk_spot()
        print(hk_index_df)
    except Exception as e:
        print(f"获取港股交易日历失败: {e}")
        results["港股"] = "获取失败"
    
    # # 美股最后交易日
    # try:
    #     us_index_df = ak.stock_us_spot_em()
    #     results["美股"] = us_index_df.index[-1].strftime("%Y-%m-%d")
    # except Exception as e:
    #     print(f"获取美股交易日历失败: {e}")
    #     results["美股"] = "获取失败"
    
    return results

# 获取并打印结果
last_trade_dates = get_last_trade_dates()
for market, date in last_trade_dates.items():
    print(f"{market}最后交易日: {date}")