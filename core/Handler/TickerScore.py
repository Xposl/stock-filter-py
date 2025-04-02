#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TickerScore处理程序 - 负责股票评分计算和数据库更新
"""

from core.Score import Score
from core.API.ticker_score_repository import TickerScoreRepository

class TickerScore:
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
        self.score_repository = TickerScoreRepository()
    
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
            None
        """
        result = self.calculate(ticker, kLineData, strategyData, indicatorData, valuationData)
        # self.score_repository.update_items(ticker.id, result)
