"""
股票数据处理模块 - 负责从各种数据源获取股票列表和详情
"""
import datetime
import logging
from time import time

from .data_sources.xueqiu_api import Xueqiu
from core.utils import UtilsHelper
from core.service.ticker_repository import TickerRepository
from .utils import retry_on_exception
from .dongcai_ticker import DongCaiTicker

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class Ticker:
    """股票数据处理类"""
    
    def __init__(self, update_time):
        """初始化股票数据处理类
        
        Args:
            update_time: 更新时间字符串
        """
        self.sources = [DongCaiTicker()]
        self.update_time = update_time
        self.ticker_repository = TickerRepository()
        self.xueqiu = Xueqiu()

    def update_ticker_list(self):
        """更新股票列表
        
        Returns:
            dict: 以股票代码为键的股票信息字典
        """
        data = {}
        for source in self.sources:
            tickers = source.update_tickers()
            for ticker in tickers:
                code = ticker["code"]
                if code not in data:
                    data[code] = ticker
        return data

    @retry_on_exception(max_retries=3, delay=5, backoff=2)
    def update_ticker_detail(self, code, name):
        """更新单个股票详情
        
        Args:
            code: 股票代码
            name: 股票名称
            
        Returns:
            dict: 股票详细信息
        """
        try:
            ticker_info = self.xueqiu.getStockDetail(code, name)
            if ticker_info is not None:
                ticker_info["type"] = ticker_info["type"].value
            return ticker_info
        except Exception as e:
            logger.error(f"获取股票详情出错 ({code}): {str(e)}")
            raise

    def get_ticker_detail(self, ticker_info):
        """获取股票详情
        
        Args:
            ticker_info: 股票信息字典
            
        Returns:
            dict: 更新后的股票详细信息
        """
        try:
            new_ticker = self.update_ticker_detail(ticker_info["code"], ticker_info["name"])
            if new_ticker is None:
                logger.warning(f"无法获取股票详情: {ticker_info["code"]}")
                return None
            
            # 只保留数据库中存在的字段
            allowed_fields = [
                "code", "name", "group_id", "type", "source", "status", 
                "is_deleted", "time_key", "open", "close", "high", "low", 
                "volume", "turnover", "turnover_rate", "update_date", 
                "listed_date", "pe_forecast", "pettm", "pb", "total_share",
                "lot_size", "modify_time", "remark"
            ]
            
            filtered_ticker = {k: v for k, v in new_ticker.items() if k in allowed_fields}
            
            filtered_ticker["modify_time"] = datetime.datetime.now().strftime("%Y-%m-%d")
            filtered_ticker["source"] = ticker_info.get("source", 1)
                
            return filtered_ticker
        except Exception as e:
            logger.error(f"获取股票详情出错: {ticker_info["code"]} - {str(e)}")
            return None

    def update_tickers(self):
        """更新所有股票数据并插入到数据库
        
        Returns:
            bool: 更新是否成功
        """
        try:
            # 获取最新的股票列表
            ticker_list = self.update_ticker_list()
            # 获取现有的股票数据
            existing_tickers = self.ticker_repository.get_all_map()
            
            # 使用单独的数据库连接进行批量处理，避免锁冲突
            db_adapter = self.ticker_repository.db
            
            # 处理新增和更新股票
            processed_count = 0
            total = len(ticker_list)
            batch_size = 5  # 减小批处理大小，更频繁地提交事务
            
            # 确保开始一个新的事务
            try:
                db_adapter.rollback()  # 清除任何可能存在的未完成事务
            except:
                pass
                
            for i, code in enumerate(ticker_list):
                try:
                    UtilsHelper().runProcess(i, total, "处理项目", f"{code}")
                    ticker = ticker_list[code]
                    
                    if code not in existing_tickers:
                        # 获取新股详情
                        new_ticker = self.get_ticker_detail(ticker)
                        if new_ticker:
                            self.ticker_repository.create(
                                new_ticker["code"], 
                                new_ticker["name"], 
                                new_ticker, 
                                commit=False
                            )
                            processed_count += 1
                    elif ticker.get("name") != existing_tickers[code].get("name"):
                        new_ticker = self.get_ticker_detail(ticker)
                        if new_ticker:
                            self.ticker_repository.update(
                                new_ticker["code"], 
                                new_ticker["name"], 
                                new_ticker, 
                                commit=False
                            )

                    # 每处理batch_size条记录提交一次
                    if (i + 1) % batch_size == 0:
                        try:
                            db_adapter.commit()
                            time.sleep(0.1)  # 短暂暂停
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
                if code not in ticker_list:
                    UtilsHelper().runProcess(i, len(existing_tickers), "删除项目", f"{code}")
                    self.ticker_repository.update(
                        code, 
                        existing_tickers[code]["name"], 
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
