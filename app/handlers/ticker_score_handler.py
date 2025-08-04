"""
股票评分处理器
负责股票评分的计算和数据库更新
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from app.entities.ticker_score import TickerScore, TickerScoreCreate, TickerScoreUpdate
from app.entities.ticker import Ticker
from app.handlers.base_handler import BaseHandler
from app.repositories.ticker_score_repository import TickerScoreRepository
from app.services.database_service import get_database_service
from core.schema.k_line import KLine
from core.score import Score


class TickerScoreHandler(BaseHandler):
    """
    股票评分处理器类
    负责股票评分的计算、更新和管理
    """
    
    def __init__(self, rule: Optional[List] = None):
        """
        初始化处理器
        
        Args:
            rule: 评分规则列表
        """
        super().__init__()
        self.db_service = get_database_service()
        self.score_repo = TickerScoreRepository(self.db_service)
        self.rule = rule
    
    def set_rule(self, rule: List):
        """设置评分规则"""
        self.rule = rule
    
    def calculate(
        self,
        ticker: Ticker,
        kl_data: List[KLine],
        strategy_data: Optional[List] = None,
        indicator_data: Optional[List] = None,
        valuation_data: Optional[List] = None,
    ) -> List[TickerScore]:
        """
        计算股票评分
        
        Args:
            ticker: 股票对象
            kl_data: K线数据列表
            strategy_data: 策略数据（可选）
            indicator_data: 指标数据（可选）
            valuation_data: 估值数据（可选）
            
        Returns:
            评分结果列表
        """
        if not self.rule:
            raise ValueError("评分规则未设置")
        
        return Score(self.rule).calculate(
            ticker, kl_data, strategy_data, indicator_data, valuation_data
        )
    
    async def update_ticker_score(
        self,
        ticker: Ticker,
        kl_data: List[KLine],
        strategy_data: Optional[List] = None,
        indicator_data: Optional[List] = None,
        valuation_data: Optional[List] = None,
    ) -> List[TickerScore]:
        """
        更新股票评分
        
        Args:
            ticker: 股票对象
            kl_data: K线数据列表
            strategy_data: 策略数据（可选）
            indicator_data: 指标数据（可选）
            valuation_data: 估值数据（可选）
            
        Returns:
            评分结果列表
        """
        # 计算所有K线的评分结果
        result = self.calculate(
            ticker, kl_data, strategy_data, indicator_data, valuation_data
        )
        
        if not result or len(result) == 0:
            self.logger.warning(f"股票 {ticker.code} 无评分结果")
            return result
        
        # 按照时间排序结果（确保最新数据在最后）
        result.sort(key=lambda x: x.time_key)
        
        # 获取最新的一条记录
        latest_score = result[-1]
        
        # 更新数据库
        await self._update_score_in_db(ticker.id, latest_score)
        
        return result
    
    async def _update_score_in_db(self, ticker_id: int, score: TickerScore):
        """
        更新数据库中的评分数据
        
        Args:
            ticker_id: 股票ID
            score: 评分对象
        """
        try:
            # 检查是否已存在
            existing_score = await self.score_repo.get_by_ticker_and_time(
                ticker_id, score.time_key
            )
            
            if existing_score:
                # 更新现有记录
                update_data = TickerScoreUpdate(
                    score_value=score.score_value,
                    score_type=score.score_type,
                    score_data=score.score_data,
                    version=existing_score.version + 1
                )
                await self.score_repo.update(existing_score.id, update_data)
                self.logger.info(f"更新评分 {score.time_key} 成功")
            else:
                # 创建新记录
                create_data = TickerScoreCreate(
                    ticker_id=ticker_id,
                    time_key=score.time_key,
                    score_value=score.score_value,
                    score_type=score.score_type,
                    score_data=score.score_data,
                    code=f"{ticker_id}_{score.time_key}"
                )
                await self.score_repo.create(create_data)
                self.logger.info(f"创建评分 {score.time_key} 成功")
                
        except Exception as e:
            self.logger.error(f"更新评分 {score.time_key} 失败: {str(e)}")
            raise
    
    async def get_ticker_scores(
        self, 
        ticker_id: int, 
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        score_type: Optional[str] = None
    ) -> List[TickerScore]:
        """
        获取股票评分列表
        
        Args:
            ticker_id: 股票ID
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）
            score_type: 评分类型（可选）
            
        Returns:
            评分列表
        """
        return await self.score_repo.get_by_ticker_id(
            ticker_id, start_time, end_time, score_type
        )
    
    async def get_latest_score(
        self, 
        ticker_id: int, 
        score_type: Optional[str] = None
    ) -> Optional[TickerScore]:
        """
        获取最新评分
        
        Args:
            ticker_id: 股票ID
            score_type: 评分类型（可选）
            
        Returns:
            最新评分对象或None
        """
        return await self.score_repo.get_latest_by_ticker(ticker_id, score_type)
    
    async def get_score_by_time(
        self, 
        ticker_id: int, 
        time_key: str
    ) -> Optional[TickerScore]:
        """
        根据时间获取评分
        
        Args:
            ticker_id: 股票ID
            time_key: 时间键
            
        Returns:
            评分对象或None
        """
        return await self.score_repo.get_by_ticker_and_time(ticker_id, time_key)
    
    async def delete_score(
        self, 
        ticker_id: int, 
        time_key: str
    ) -> bool:
        """
        删除评分
        
        Args:
            ticker_id: 股票ID
            time_key: 时间键
            
        Returns:
            是否删除成功
        """
        score = await self.get_score_by_time(ticker_id, time_key)
        if score:
            await self.score_repo.delete(score.id)
            self.logger.info(f"删除评分 {time_key} 成功")
            return True
        return False
    
    async def get_score_statistics(
        self, 
        ticker_id: int, 
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取评分统计信息
        
        Args:
            ticker_id: 股票ID
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）
            
        Returns:
            统计信息字典
        """
        scores = await self.get_ticker_scores(ticker_id, start_time, end_time)
        
        if not scores:
            return {
                "count": 0,
                "avg_score": 0,
                "max_score": 0,
                "min_score": 0,
                "latest_score": None
            }
        
        score_values = [score.score_value for score in scores if score.score_value is not None]
        
        return {
            "count": len(scores),
            "avg_score": sum(score_values) / len(score_values) if score_values else 0,
            "max_score": max(score_values) if score_values else 0,
            "min_score": min(score_values) if score_values else 0,
            "latest_score": scores[-1] if scores else None
        }


# 单例模式
_ticker_score_handler_instance = None


def get_ticker_score_handler(rule: Optional[List] = None) -> TickerScoreHandler:
    """获取TickerScoreHandler单例实例"""
    global _ticker_score_handler_instance
    if _ticker_score_handler_instance is None:
        _ticker_score_handler_instance = TickerScoreHandler(rule)
    elif rule is not None:
        _ticker_score_handler_instance.set_rule(rule)
    return _ticker_score_handler_instance 