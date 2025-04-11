#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TickerScore处理程序 - 负责股票评分计算和数据库更新
"""

from core.score import Score
from core.service.ticker_score_repository import TickerScoreRepository

class TickerScoreHandler:
    """
    股票评分处理类，用于计算并更新股票评分数据
    """
    rule = None
    
    def __init__(self, rule=None):
        """
        初始化TickerScore
        
        Args:
            rule: 可选评分规则，默认使用NormalScore
        """
        if rule is not None:
            self.rule = rule
    
    def calculate(self, ticker, kLineData, strategyData, indicatorData, valuationData):
        """
        计算股票评分
        
        Args:
            ticker: 股票数据
            kLineData: K线数据
            strategyData: 策略数据
            indicatorData: 指标数据
            valuationData: 估值数据
            
        Returns:
            评分结果列表
        """
        return Score(self.rule).calculate(ticker, kLineData, strategyData, indicatorData, valuationData)
    
    def update_ticker_score(self, ticker, kLineData, strategyData, indicatorData, valuationData):
        """
        更新股票评分
        
        Args:
            ticker: 股票数据
            kLineData: K线数据
            strategyData: 策略数据
            indicatorData: 指标数据
            valuationData: 估值数据
            
        Returns:
            评分结果列表
        """
        # 计算所有K线的评分结果
        result = self.calculate(ticker, kLineData, strategyData, indicatorData, valuationData)
        
        if not result or len(result) == 0:
            return result
        
        # 按照时间排序结果（确保最新数据在最后）
        result.sort(key=lambda x: x['time_key'])
        
        # 获取最新的一条记录
        latest_score = result[-1].copy()
        
        # 将除了最新记录之外的所有记录作为历史数据
        history_data = result[:-1] if len(result) > 1 else []
        
        # 在最新记录中添加历史数据
        latest_score['history'] = history_data
        
        # 只更新最新的一条记录到数据库
        TickerScoreRepository().update_items(ticker.id, [latest_score])
        
        return result
