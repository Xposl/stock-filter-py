"""
股票数据处理模块 - 负责从各种数据源获取股票列表和详情
"""

import akshare as ak
import datetime
import logging
import time
import random
from functools import wraps

from core.API import APIHelper
from core.API.Helper.XueqiuHelper import Xueqiu
from core.utils import UtilsHelper
from core.API.TickerRepository import TickerRepository

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 重试装饰器
def retry_on_exception(max_retries=3, delay=5, backoff=2, exceptions=(Exception,)):
    """
    重试函数执行的装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟时间的倍数增长
        exceptions: 需要捕获的异常类型
        
    Returns:
        函数执行结果或者在达到最大重试次数后抛出异常
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            mtries, mdelay = max_retries, delay
            while mtries > 0:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    mtries -= 1
                    if mtries == 0:
                        logger.error(f"函数 {func.__name__} 达到最大重试次数 {max_retries}")
                        raise
                    
                    # 添加随机抖动，避免同时重试
                    jitter = random.uniform(0.1, 0.5)
                    sleep_time = mdelay + jitter
                    
                    logger.warning(f"函数 {func.__name__} 调用失败，错误: {str(e)}")
                    logger.warning(f"将在 {sleep_time:.2f} 秒后重试，剩余重试次数: {mtries}")
                    
                    time.sleep(sleep_time)
                    mdelay *= backoff
        return wrapper
    return decorator

class DongCaiTicker:
    """东财数据源股票获取类"""
    
    @retry_on_exception(max_retries=3, delay=5, backoff=2)
    def get_ch_tickers(self):
        """
        获取中国A股股票列表
        
        Returns:
            list: 包含所有A股股票信息的列表
        """
        result = []
        tickers = ak.stock_zh_a_spot_em()
        for i in range(len(tickers)):
            code = tickers['代码'][i]
            if code.startswith('0') or code.startswith('3'):
                code  = 'SZ.%s'%str(code)
            elif code.startswith('6') or code.startswith('7') or code.startswith('9'):
                code  = 'SH.%s'%str(code)
            elif code.startswith('83') or code.startswith('87') or code.startswith('88'):
                code  = 'BJ.%s'%str(code)
                ## TODO: 跳过北交所
                continue
            else:
                continue

            result.append({
                'code': code,
                'name': tickers['名称'][i],
                'source': 1
            })
        return result

    @retry_on_exception(max_retries=3, delay=5, backoff=2)
    def get_hk_tickers(self):
        """
        获取香港股票列表
        
        Returns:
            list: 包含所有港股的列表
        """
        result = []
        tickers = ak.stock_hk_spot_em()
        for i in range(len(tickers)):
            result.append({
                'code': 'HK.%s'%tickers['代码'][i],
                'name': tickers['名称'][i],
                'source': 1
            })
        return result

    @retry_on_exception(max_retries=3, delay=5, backoff=2)
    def get_us_tickers(self):
        """
        获取美国股票列表
        
        Returns:
            list: 包含所有美股的列表
        """
        result = []
        tickers = ak.stock_us_spot_em()
        for i in range(len(tickers)):
            result.append({
                'code': 'US.%s'%tickers['代码'][i][4:],
                'name': tickers['名称'][i],
                'source': 1
            })
        return result

    def update_tickers(self):
        """
        获取所有股票列表
        
        Returns:
            list: 包含所有股票的列表
        """
        result = []
        result += self.get_hk_tickers()
        result += self.get_us_tickers()
        result += self.get_ch_tickers()
        return result


class Ticker:
    """股票数据处理类"""
    Xueqiu = Xueqiu()
    
    def __init__(self, update_time):
        """
        初始化股票数据处理类
        
        Args:
            update_time: 更新时间
        """
        self.source = []
        self.source.append(DongCaiTicker())
        self.update_time = update_time
        self.api_helper = APIHelper()
        self.ticker_repository = TickerRepository()

    def update_ticker_list(self):
        """
        更新股票列表
        
        Returns:
            dict: 以股票代码为键的股票信息字典
        """
        data = {}
        for source in self.source:
            tickers = source.update_tickers()
            for ticker in tickers:
                code = ticker['code']
                if code not in data:
                    data[code] = ticker
        return data

    @retry_on_exception(max_retries=3, delay=5, backoff=2)
    def update_ticker_detail(self, code, name):
        """
        更新单个股票详情
        
        Args:
            code: 股票代码
            name: 股票名称
            
        Returns:
            dict: 股票详细信息
        """
        try:
            ticker = self.Xueqiu.getStockDetail(code, name)
            if ticker is not None:
                ticker['type'] = ticker['type'].value
            return ticker
        except Exception as e:
            logger.error(f"获取股票详情出错 ({code}): {str(e)}")
            raise  # 重新抛出异常，让重试装饰器处理
    
    def get_ticker_detail(self, ticker):
        """
        获取股票详情
        
        Args:
            ticker: 股票信息字典
            
        Returns:
            dict: 更新后的股票详细信息
        """
        try:
            new_ticker = self.update_ticker_detail(ticker['code'], ticker['name'])
            if new_ticker is None:
                logger.warning(f"无法获取股票详情: {ticker['code']}")
                return None
            
            # 只保留数据库中存在的字段
            allowed_fields = [
                'code', 'name', 'group_id', 'type', 'source', 'status', 
                'is_deleted', 'time_key', 'open', 'close', 'high', 'low', 
                'volume', 'turnover', 'turnover_rate', 'update_date', 
                'listed_date', 'pe_forecast', 'pettm', 'pb', 'total_share',
                'lot_size', 'modify_time', 'remark'
            ]
            
            filtered_ticker = {k: v for k, v in new_ticker.items() if k in allowed_fields}
            
            filtered_ticker['modify_time'] = datetime.datetime.now().strftime('%Y-%m-%d')
            if 'source' not in ticker or ticker['source'] is None:
                filtered_ticker['source'] = 1
            else:
                filtered_ticker['source'] = ticker['source']
                
            return filtered_ticker
        except Exception as e:
            logger.error(f"获取股票详情出错: {ticker['code']} - {str(e)}")
            return None
    
    def update_tickers(self):
        """
        更新所有股票数据并插入到 investNote.db
        """
        try:
            # 获取最新的股票列表
            ticker_list = self.update_ticker_list()
            # 获取现有的股票数据
            existing_tickers = self.ticker_repository.get_all_map()
            
            # 处理新增股票
            i = 0
            total = len(ticker_list)
            for code in ticker_list:
                UtilsHelper().runProcess(i, total, "添加新股", f"{code}")
                if code not in existing_tickers:
                    ticker = ticker_list[code]
                    # 获取新股详情
                    new_ticker = self.get_ticker_detail(ticker)
                    if new_ticker:
                        # 使用 TickerRepository 插入数据到 investNote.db，不立即提交
                        self.ticker_repository.create(
                            new_ticker['code'], 
                            new_ticker['name'], 
                            new_ticker, 
                            commit=False  # 不立即提交，使用批量事务
                        )
                
                    i += 1  # 需要更新才增加计数器
                
                # 每处理10条记录提交一次，平衡性能和内存占用
                if i % 10 == 0:
                    try:
                        self.ticker_repository.db.commit()
                        # SQLite会在下一次执行SQL时自动开始新事务，无需显式调用begin
                    except Exception as e:
                        logger.error(f"提交批量数据出错: {str(e)}")
                        self.ticker_repository.db.rollback()
                        # SQLite会在下一次执行SQL时自动开始新事务，无需显式调用begin
            
            # 提交最后一批数据
            if total > 0:
                try:
                    self.ticker_repository.db.commit()
                except Exception as e:
                    logger.error(f"提交最终数据出错: {str(e)}")
                    self.ticker_repository.db.rollback()

            # 处理需要更新的股票
            i = 0
            existing_ticker_dict = {k: v.model_dump() for k, v in existing_tickers.items()}
            total = len(existing_ticker_dict)
            current_date = datetime.datetime.now().strftime('%Y-%m-%d')
            
            for code, ticker in existing_ticker_dict.items():
                UtilsHelper().runProcess(i, total, "更新现有股", f"{code}")
                
                # 需要更新的情况：1. 股票不在最新列表且修改时间早于今天; 2. 股票在列表中但名称变了
                modify_time = ticker.get('modify_time')
                if modify_time and isinstance(modify_time, datetime.datetime):
                    modify_time_str = modify_time.strftime('%Y-%m-%d')
                else:
                    modify_time_str = str(modify_time)
                
                need_update = False
                if code not in ticker_list and modify_time_str < current_date:
                    need_update = True
                elif code in ticker_list and ticker.get('name') != ticker_list[code].get('name'):
                    need_update = True
                    
                if need_update:
                    logger.info(f'更新项目: {code}')
                    new_ticker = self.get_ticker_detail(ticker)
                    if new_ticker:
                        # 使用 TickerRepository 更新数据到 investNote.db
                        self.ticker_repository.update(new_ticker['code'], new_ticker['name'], new_ticker)
                
                i += 1
                
            logger.info("股票数据更新完成")
            return True
            
        except Exception as e:
            logger.error(f"更新股票数据出错: {str(e)}")
            # 发生错误时回滚事务
            self.ticker_repository.db.rollback()
            return False
