#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TickerScore处理程序 - 负责股票评分计算和数据库更新
"""

from typing import List, Optional
from core.models.ticker import Ticker
from core.models.ticker_score import TickerScore
from core.schema.k_line import KLine
from core.score import Score
from core.service.ticker_score_repository import TickerScoreRepository

class TickerScoreHandler:
    """
    股票评分处理类，用于计算并更新股票评分数据
    """
    rule = None
    
    def __init__(self, rule: Optional[list]=None):
        """
        初始化TickerScore
        
        Args:
            rule: 可选评分规则
        """
        if rule is not None:
            self.rule = rule
    
    def calculate(self, ticker: Ticker, kl_data: List[KLine], strategyData: Optional[list]=None, indicatorData: Optional[list]=None, valuationData: Optional[list]=None) -> List[TickerScore]:
        """
        计算股票评分
        
        Args:
            ticker: 股票数据
            kl_data: K线数据
            strategyData: 策略数据
            indicatorData: 指标数据
            valuationData: 估值数据
            
        Returns:
            评分结果列表
        """
        return Score(self.rule).calculate(ticker, kl_data, strategyData, indicatorData, valuationData)
    
    def update_ticker_score(self, ticker : Ticker, kl_data: List[KLine], strategyData: Optional[list]=None, indicatorData: Optional[list]=None, valuationData: Optional[list]=None) -> List[TickerScore]:
        """
        更新股票评分
        
        Args:
            ticker: 股票数据
            kl_data: K线数据
            strategyData: 策略数据
            indicatorData: 指标数据
            valuationData: 估值数据
            
        Returns:
            评分结果列表
        """
        # 计算所有K线的评分结果
        result = self.calculate(ticker, kl_data , strategyData, indicatorData, valuationData)
        
        if not result or len(result) == 0:
            return result
        
        # 按照时间排序结果（确保最新数据在最后）
        result.sort(key=lambda x: x.time_key)
        
        # 获取最新的一条记录
        latest_score = result[-1]
        
        # 将TickerScore对象转换为字典格式用于数据库更新
        from core.models.ticker_score import ticker_score_to_dict
        latest_score_dict = ticker_score_to_dict(latest_score)
        
        # 只更新最新的一条记录到数据库
        TickerScoreRepository().update_items(ticker.id, [latest_score_dict])
        
        return result
