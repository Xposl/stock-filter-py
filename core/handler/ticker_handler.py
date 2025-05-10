"""
股票数据处理模块 - 负责从各种数据源获取股票列表和详情
"""
import logging
import os
from time import sleep
from typing import Dict, Optional

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
                    UtilsHelper().runProcess(i, total, "处理项目", f"{code}")
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
                            logger.error(f"提交批量数据出错: {str(e)}")
                            db_adapter.rollback()
                            
                except Exception as e:
                    logger.error(f"处理股票 {code} 时出错: {str(e)}")
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
                    UtilsHelper().runProcess(i, len(existing_tickers), "删除项目", f"{code}")
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
