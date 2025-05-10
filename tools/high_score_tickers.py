#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
获取高评分股票的工具

通过此模块可以获取 A 股、港股和美股中评分大于特定阈值的股票列表
支持将结果导出为JSON文件
"""

import os
import json
import datetime
from typing import Dict, List, Tuple, Optional
from core.service.ticker_repository import TickerRepository
from core.service.ticker_score_repository import TickerScoreRepository
from core.models.ticker import Ticker
from core.models.ticker_score import TickerScore
from core.enum.ticker_group import TickerGroup

def get_high_score_tickers(min_score: float = 75.0, as_dict: bool = False) -> Dict[str, List]:
    """
    获取 A 股、港股和美股中评分大于指定阈值的股票列表
    
    Args:
        min_score: 评分阈值，默认为 75.0
    
    Returns:
        按市场分组的高评分股票列表，格式为 {'A股': [...], '港股': [...], '美股': [...]}
    """
    # 获取所有可用股票
    ticker_repo = TickerRepository()
    all_tickers = ticker_repo.get_all_available()
    
    # 结果字典
    result = {
        "A股": [],
        "港股": [],
        "美股": []
    }
    
    # 评分仓库
    score_repo = TickerScoreRepository()
    
    # 遍历所有股票
    for ticker in all_tickers:
        # 获取股票评分记录
        score_records = score_repo.get_items_by_ticker_id(ticker.id)
        
        # 如果没有评分记录，跳过
        if not score_records:
            continue
        
        # 获取最新的评分记录（排序在 get_items_by_ticker_id 中已完成，最新的记录在列表首位）
        latest_score = score_records[0]
        
        # 如果评分大于阈值，则添加到结果中
        if latest_score.score >= min_score:
            # 根据 group_id 确定市场
            if ticker.group_id == TickerGroup.ZH.value:
                result["A股"].append((ticker, latest_score))
            elif ticker.group_id == TickerGroup.HK.value:
                result["港股"].append((ticker, latest_score))
            elif ticker.group_id == TickerGroup.US.value:
                result["美股"].append((ticker, latest_score))
    
    # 对每个市场的结果按照评分降序排序
    for market in result:
        result[market].sort(key=lambda x: x[1].score, reverse=True)
    
    # 如果需要字典格式（用于JSON导出），转换数据结构
    if as_dict:
        dict_result = {}
        for market, tickers in result.items():
            dict_result[market] = []
            for ticker, score in tickers:
                dict_result[market].append({
                    "id": ticker.id,
                    "code": ticker.code,
                    "name": ticker.name,
                    "score": score.score,
                    "ma_score": score.ma_score,
                    "in_score": score.in_score,
                    "strategy_score": score.strategy_score,
                    "time_key": score.time_key
                })
        return dict_result
                
    return result

def export_high_score_tickers_to_json(min_score: float = 75.0, file_path: Optional[str] = None) -> str:
    """
    将高评分股票数据导出到JSON文件
    
    Args:
        min_score: 评分阈值，默认为 75.0
        file_path: 导出文件路径，如果为None则自动生成
    
    Returns:
        导出文件的路径
    """
    # 获取高评分股票数据（转换为可JSON序列化的字典格式）
    result = get_high_score_tickers(min_score, as_dict=True)
    
    # 添加元数据
    output_data = {
        "meta": {
            "min_score": min_score,
            "export_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_count": sum(len(tickers) for tickers in result.values())
        },
        "data": result
    }
    
    # 如果未指定文件路径，自动生成一个
    if file_path is None:
        # 确保output目录存在
        os.makedirs("output", exist_ok=True)
        
        # 生成文件名
        date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"output/high_score_tickers_{date_str}.json"
    
    # 写入JSON文件
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)
    
    return file_path

def print_high_score_tickers(min_score: float = 75.0, export_json: bool = False, file_path: Optional[str] = None) -> Optional[str]:
    """
    打印每个市场中高于指定评分的股票列表
    
    Args:
        min_score: 评分阈值，默认为 75.0
    
    Returns:
        None
    """
    result = get_high_score_tickers(min_score)
    
    # 打印每个市场的高评分股票
    for market, tickers in result.items():
        print(f"\n{market} 评分 >= {min_score} 的股票列表 ({len(tickers)} 只):")
        print("-" * 60)
        print(f"{'代码':<10}{'名称':<16}{'评分':<10}{'时间':<20}")
        print("-" * 60)
        
        for ticker, score in tickers:
            print(f"{ticker.code:<10}{ticker.name:<16}{score.score:<10.2f}{score.time_key:<20}")
    
    # 打印总计
    total = sum(len(tickers) for tickers in result.values())
    print(f"\n总计: {total} 只股票的评分 >= {min_score}")
    
    # 如果需要导出JSON，执行导出
    if export_json:
        json_path = export_high_score_tickers_to_json(min_score, file_path)
        print(f"\n已导出到JSON文件: {json_path}")
        return json_path
    
    return None

# 示例用法
if __name__ == "__main__":
    import sys
    
    # 解析命令行参数
    min_score = 75.0
    export_json = False
    
    if len(sys.argv) > 1:
        try:
            min_score = float(sys.argv[1])
        except ValueError:
            print(f"警告: 无效的评分阈值 '{sys.argv[1]}'，使用默认值 75.0")
    
    if len(sys.argv) > 2 and sys.argv[2].lower() in ('export', 'json', 'true', '1'):
        export_json = True
    
    # 获取评分大于指定阈值的股票列表并打印
    print_high_score_tickers(min_score, export_json)
