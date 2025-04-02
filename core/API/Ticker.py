#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
提供传统 Ticker API 兼容层

此模块为旧版 API 提供兼容性接口，内部使用 TickerRepository 实现功能
"""

import copy
import datetime
import logging
from typing import Dict, List, Any, Optional, Union

from ..DB.DBAdapter import DBAdapter
from .TickerRepository import TickerRepository
from core.models.ticker import Ticker as TickerModel, dict_to_ticker

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Ticker:
    """传统 Ticker API 兼容类"""
    
    def __init__(self, db_connection=None):
        """
        初始化 Ticker API
        
        Args:
            db_connection: 数据库连接
        """
        self.repository = TickerRepository(db_connection)
    
    def getAllItems(self) -> List[Dict]:
        """
        获取所有股票
        
        Returns:
            股票列表
        """
        try:
            tickers = self.repository.get_all()
            return [ticker.model_dump() for ticker in tickers]
        except Exception as e:
            logger.error(f"获取所有股票失败: {e}")
            return []
    
    def getAllMapItems(self) -> Dict[str, Dict]:
        """
        获取所有股票，以代码为键
        
        Returns:
            以代码为键的股票字典
        """
        try:
            ticker_map = self.repository.get_all_map()
            return {code: ticker.model_dump() for code, ticker in ticker_map.items()}
        except Exception as e:
            logger.error(f"获取股票映射失败: {e}")
            return {}
    
    def getAllAvaiableItems(self, end_date: Optional[str] = None) -> List[Dict]:
        """
        获取所有可用股票
        
        Args:
            end_date: 结束日期
            
        Returns:
            可用股票列表
        """
        try:
            tickers = self.repository.get_all_available(end_date)
            return [ticker.model_dump() for ticker in tickers]
        except Exception as e:
            logger.error(f"获取可用股票失败: {e}")
            return []
    
    def getAllAvaiableItemsQuarter(self, end_time: str, page: int) -> List[Dict]:
        """
        分页获取可用股票
        
        Args:
            end_time: 结束时间
            page: 页码
            
        Returns:
            股票列表
        """
        try:
            tickers = self.repository.get_all_available_quarter(end_time, page)
            return [ticker.model_dump() for ticker in tickers]
        except Exception as e:
            logger.error(f"分页获取股票失败: {e}")
            return []
    
    def getAllAvaiableItemsStartWith(self, start_key: str) -> List[Dict]:
        """
        获取以指定字符串开头的所有可用股票
        
        Args:
            start_key: 股票代码开头字符串
            
        Returns:
            股票列表
        """
        try:
            tickers = self.repository.get_all_available_start_with(start_key)
            return [ticker.model_dump() for ticker in tickers]
        except Exception as e:
            logger.error(f"获取指定前缀股票失败: {e}")
            return []
    
    def getItemByCode(self, code: str) -> Optional[Dict]:
        """
        根据代码获取股票
        
        Args:
            code: 股票代码
            
        Returns:
            股票信息或 None
        """
        try:
            ticker = self.repository.get_by_code(code)
            return ticker.model_dump() if ticker else None
        except Exception as e:
            logger.error(f"获取股票失败: {code} - {e}")
            return None
    
    def getItemLikeCode(self, code: str) -> Optional[Dict]:
        """
        根据代码模糊查询股票
        
        Args:
            code: 股票代码
            
        Returns:
            股票信息或 None
        """
        try:
            ticker = self.repository.get_like_code(code)
            return ticker.model_dump() if ticker else None
        except Exception as e:
            logger.error(f"模糊查询股票失败: {code} - {e}")
            return None
    
    def insertItem(self, code: str, name: str, data: Dict, commit: bool = True) -> Optional[Dict]:
        """
        插入股票
        
        Args:
            code: 股票代码
            name: 股票名称
            data: 股票数据
            commit: 是否提交
            
        Returns:
            插入的股票或 None
        """
        try:
            ticker = self.repository.create(code, name, data, commit)
            return ticker.model_dump() if ticker else None
        except Exception as e:
            logger.error(f"插入股票失败: {code} - {e}")
            return None
    
    def updateItem(self, code: str, name: str, data: Dict) -> Optional[Dict]:
        """
        更新股票
        
        Args:
            code: 股票代码
            name: 股票名称
            data: 股票数据
            
        Returns:
            更新的股票或 None
        """
        try:
            ticker = self.repository.update(code, name, data)
            return ticker.model_dump() if ticker else None
        except Exception as e:
            logger.error(f"更新股票失败: {code} - {e}")
            return None
    
    def getUpdateTimeByCode(self, code: str, kl_type: str) -> Optional[datetime.datetime]:
        """
        获取股票更新时间
        
        Args:
            code: 股票代码
            kl_type: K线类型
            
        Returns:
            更新时间或 None
        """
        try:
            return self.repository.get_update_time_by_code(code, kl_type)
        except Exception as e:
            logger.error(f"获取更新时间失败: {code} - {e}")
            return None
