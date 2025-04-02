"""
股票数据处理模块 - 负责从各种数据源获取股票列表和详情
"""

import akshare as ak
import datetime
import logging

from core.API import APIHelper
from core.API.Helper.XueqiuHelper import Xueqiu
from core.utils import UtilsHelper
from core.API.TickerRepository import TickerRepository

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DongCaiTicker:
    """东财数据源股票获取类"""
    
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

    def update_ticker_detail(self, code, name):
        """
        更新单个股票详情
        
        Args:
            code: 股票代码
            name: 股票名称
            
        Returns:
            dict: 股票详细信息
        """
        ticker = Xueqiu().getStockDetail(code, name)
        if ticker is not None:
            ticker['type'] = ticker['type'].value
        return ticker
    
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
            
            # 详细记录估值相关字段
            logger.info(f"处理股票详情: {ticker['code']}, 估值数据: pe_forecast={filtered_ticker.get('pe_forecast')}, pettm={filtered_ticker.get('pettm')}, pb={filtered_ticker.get('pb')}, total_share={filtered_ticker.get('total_share')}, lot_size={filtered_ticker.get('lot_size')}")
                
            return filtered_ticker
        except Exception as e:
            logger.error(f"获取股票详情出错: {ticker['code']} - {str(e)}")
            return None
    
    def update_tickers(self):
        """
        更新所有股票数据并插入到 investNote.db
        """
        import time
        
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
                        # 添加重试机制处理数据库锁定
                        max_retries = 3
                        retries = 0
                        while retries < max_retries:
                            try:
                                # 使用 TickerRepository 插入数据到 investNote.db
                                result = self.ticker_repository.create(
                                    new_ticker['code'], 
                                    new_ticker['name'], 
                                    new_ticker, 
                                    commit=(i % 10 == 0 or i == total - 1)  # 减少提交频率
                                )
                                if result:
                                    break  # 如果成功则跳出重试循环
                            except Exception as e:
                                if "database is locked" in str(e):
                                    retries += 1
                                    logger.warning(f"数据库锁定，将在1秒后重试第{retries}次: {code}")
                                    time.sleep(1)  # 等待1秒再重试
                                else:
                                    raise  # 如果是其他错误，则抛出
                            
                            # 如果达到最大重试次数，记录警告并继续
                            if retries == max_retries:
                                logger.warning(f"添加股票失败(达到最大重试次数): {code}")
                                
                i += 1
                
                # 每添加10个股票让数据库有时间处理
                if i % 10 == 0:
                    logger.info("暂停一秒以避免数据库锁定...")
                    time.sleep(1)
            
            # 如果最后一批数据没有提交，确保提交
            if total > 0:
                try:
                    self.ticker_repository.db.commit()
                except Exception as e:
                    logger.error(f"提交最终数据出错: {str(e)}")

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
