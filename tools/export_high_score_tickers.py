#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
导出高评分股票工具

将 A 股、港股和美股中评分大于特定阈值的股票列表导出到 JSON 文件
"""

import sys
import os
import argparse
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 导入高评分股票模块
from custom.high_score_tickers import export_high_score_tickers_to_json

def main():
    """
    主函数
    """
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(description='导出高评分股票到 JSON 文件')
    parser.add_argument('-s', '--score', type=float, default=75.0, help='评分阈值，默认为75.0')
    parser.add_argument('-o', '--output', type=str, help='指定导出的 JSON 文件路径，默认为 output/high_score_tickers_日期时间.json')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 导出文件名
    output_path = args.output
    if not output_path:
        # 生成默认文件名 (output/high_score_tickers_YYYYMMDD_HHMMSS.json)
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"output/high_score_tickers_{date_str}.json"
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print(f"获取评分 >= {args.score} 的股票列表...")
    print(f"导出到文件: {output_path}")
    
    # 执行导出
    json_path = export_high_score_tickers_to_json(args.score, output_path)
    
    print(f"\n完成! 数据已导出到: {json_path}")
    print(f"文件大小: {os.path.getsize(json_path) / 1024:.2f} KB")

if __name__ == "__main__":
    main()
