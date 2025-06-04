"""
股票数据处理模块 - 负责从各种数据源获取股票列表和详情
"""
import asyncio
import logging
import os
from time import sleep
from typing import Dict, Optional, List, Any

from core.models.ticker import Ticker, ticker_to_dict
from core.utils.data_sources.xueqiu_source import XueqiuTicker
from core.utils.utils import UtilsHelper
from core.service.ticker_repository import TickerRepository
from core.utils.retry_on_exception import retry_on_exception
from core.utils.dongcai_ticker import DongCaiTicker

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
DB_TYPE = os.getenv('DB_TYPE', 'sqlite').lower()

class TickerHandler:
    """股票数据处理类"""
    
    def __init__(self):
        """初始化股票数据处理类"""
        self.sources = [DongCaiTicker()]
        self.ticker_repository = TickerRepository()
        self.xueqiu = XueqiuTicker()

    def get_tickers(self) -> Dict[str, Ticker]:
        """获取股票列表
        Returns:
            dict: 以股票代码为键的股票信息字典
        """
        data = {}
        for source in self.sources:
            tickers = source.get_tickers()
            for ticker in tickers:
                data[ticker.code] = ticker
        return data

    def update_tickers(self) -> bool:
        """更新所有股票数据并插入到数据库
        
        Returns:
            bool: 更新是否成功
        """
        try:
            # 获取最新的股票列表
            new_tickers = self.get_tickers()
            # 获取现有的股票数据
            existing_tickers = self.ticker_repository.get_all_map()
            
            # 使用单独的数据库连接进行批量处理，避免锁冲突
            db_adapter = self.ticker_repository.db
            
            # 处理新增和更新股票
            processed_count = 0
            total = len(new_tickers)
            batch_size = 5  # 减小批处理大小，更频繁地提交事务
            
            # 确保开始一个新的事务
            try:
                db_adapter.rollback()  # 清除任何可能存在的未完成事务
            except:
                pass
                
            for i, code in enumerate(new_tickers):
                try:
                    UtilsHelper().run_process(i, total, "处理项目", f"{code}")
                    ticker = new_tickers[code]
                    if code not in existing_tickers:
                        # 获取新股详情
                        new_ticker = self.xueqiu.get_ticker(ticker.code, ticker.name)
                        if new_ticker:
                            value = ticker_to_dict(new_ticker)
                            value['id'] = None
                            self.ticker_repository.create(
                                new_ticker.code, 
                                new_ticker.name, 
                                value, 
                                commit=False
                            )
                            processed_count += 1
                    elif code in existing_tickers:
                        self.ticker_repository.update(
                            code, 
                            existing_tickers[code].name, 
                            {"is_deleted": 0}
                        )
                        

                    # 每处理batch_size条记录提交一次
                    if (i + 1) % batch_size == 0:
                        try:
                            db_adapter.commit()
                            if DB_TYPE == 'sqlite':
                                sleep(0.1)  # 短暂暂停
                        except Exception as e:
                            logger.error(f"提交批量数据出错: {e}", exc_info=True)
                            db_adapter.rollback()
                            
                except Exception as e:
                    logger.error(f"处理股票 {code} 时出错: {e}", exc_info=True)
                    continue

            # 提交最后一批数据
            try:
                db_adapter.commit()
            except Exception as e:
                logger.error(f"提交最终数据出错: {str(e)}")
                db_adapter.rollback()

            # 处理已删除的股票
            for i, code in enumerate(existing_tickers):
                if code not in new_tickers:
                    UtilsHelper().run_process(i, len(existing_tickers), "删除项目", f"{code}")
                    self.ticker_repository.update(
                        code, 
                        existing_tickers[code].name, 
                        {"is_deleted": 1}
                    )
            
            return True
            
        except Exception as e:
            logger.error(f"更新股票数据出错: {str(e)}")
            try:
                self.ticker_repository.db.rollback()
            except:
                pass
            return False
        
    async def get_ticker_by_code(self, code: str) -> Optional[Ticker]:
        """
        根据股票代码获取股票信息
        
        Args:
            code: 股票代码
            
        Returns:
            Ticker对象或None
        """
        try:
            return self.ticker_repository.get_by_code(code)
        except Exception as e:
            logger.error(f"获取股票信息失败 {code}: {e}")
            return None
    
    async def get_ticker_data(self, code: str, days: int = 30) -> Optional[List[Dict[str, Any]]]:
        """
        获取股票的评分数据
        
        Args:
            code: 股票代码
            days: 获取多少天的数据
            
        Returns:
            包含评分数据的列表，每个元素包含score等字段
        """
        try:
            # 这里简化实现，实际应该从ticker_score_repository获取数据
            # 暂时返回空列表，避免阻塞流程
            logger.debug(f"获取股票评分数据: {code}, {days}天")
            
            # TODO: 实现真正的评分数据获取逻辑
            # from core.service.ticker_score_repository import TickerScoreRepository
            # score_repo = TickerScoreRepository()
            # return score_repo.get_scores_by_code(code, days)
            
            return []
        except Exception as e:
            logger.error(f"获取股票评分数据失败 {code}: {e}")
            return None

