#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from typing import List, Dict, Any, Optional

from core.DB.DBAdapter import DBAdapter
from core.Indicator import Indicator
from core.models.ticker_indicator import (
    TickerIndicator as TickerIndicatorModel,
    TickerIndicatorCreate,
    TickerIndicatorUpdate,
    ticker_indicator_to_dict,
    dict_to_ticker_indicator
)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TickerIndicatorRepository:
    """
    使用Pydantic模型的TickerIndicator仓库类
    """
    table = 'ticker_indicator'

    def __init__(self, db_connection: Optional[Any] = None):
        """
        初始化TickerIndicator仓库
        
        Args:
            db_connection: 可选的数据库连接，如果未提供将使用DBAdapter创建新连接
        """
        if db_connection:
            self.db = db_connection
        else:
            self.db = DBAdapter()
        
        # 指标工具类
        self.indicator_helper = Indicator()

    def get_items_by_ticker_id(self, ticker_id: int, kl_type: str) -> List[TickerIndicatorModel]:
        """根据股票ID和K线类型获取所有指标记录

        Args:
            ticker_id: 股票ID
            kl_type: K线类型

        Returns:
            指标记录列表
        """
        try:
            # 使用指标键名，不再需要联表查询
            sql = f"SELECT * FROM {self.table} WHERE ticker_id = ? and kl_type = ?"
            results = self.db.query(sql, (ticker_id, kl_type))
            return [dict_to_ticker_indicator(item) for item in results]
        except Exception as e:
            logger.error(f"获取指标记录列表错误: {e}")
            return []
    
    def get_update_time_by_ticker_id(self, ticker_id: int, kl_type: str) -> Optional[str]:
        """获取股票指标最早更新时间

        Args:
            ticker_id: 股票ID
            kl_type: K线类型

        Returns:
            时间字符串
        """
        try:
            sql = f"SELECT min(time_key) as time FROM {self.table} WHERE ticker_id = ? AND kl_type = ?"
            result = self.db.query_one(sql, (ticker_id, kl_type))
            return result['time'] if result and 'time' in result else None
        except Exception as e:
            logger.error(f"获取更新时间错误: {e}")
            return None

    def get_item_by_ticker_id_and_indicator_key(self, ticker_id: int, indicator_key: str, kl_type: str) -> Optional[TickerIndicatorModel]:
        """根据股票ID, 指标键和K线类型获取指标记录

        Args:
            ticker_id: 股票ID
            indicator_key: 指标键
            kl_type: K线类型

        Returns:
            指标记录或None
        """
        try:
            sql = f"SELECT * FROM {self.table} WHERE ticker_id = ? AND indicator_key = ? AND kl_type = ?"
            result = self.db.query_one(sql, (ticker_id, indicator_key, kl_type))
            return dict_to_ticker_indicator(result) if result else None
        except Exception as e:
            logger.error(f"获取指标记录错误: {e}")
            return None

    def update_item(self, ticker_id: int, indicator_key: str, kl_type: str, time_key: str, entity: Dict[str, Any]) -> None:
        """更新或创建指标记录

        Args:
            ticker_id: 股票ID
            indicator_key: 指标键
            kl_type: K线类型
            time_key: 时间键
            entity: 指标数据

        Returns:
            None
        """
        try:
            # 检查是否存在该记录
            existing_item = self.get_item_by_ticker_id_and_indicator_key(ticker_id, indicator_key, kl_type)
            
            # 准备数据
            history_data = entity.get('history')
            
            # 直接存储为序列化数据，Pydantic模型会处理JSON序列化
            entity_data = {
                'ticker_id': ticker_id,
                'indicator_key': indicator_key,
                'kl_type': kl_type,
                'time_key': time_key,
                'history': history_data,
                'status': entity.get('status', 1)
            }

            if existing_item is None:
                # 创建新记录
                ticker_indicator = TickerIndicatorCreate(**entity_data)
                db_data = ticker_indicator_to_dict(ticker_indicator)
                
                # 构建SQL参数和占位符
                fields = []
                placeholders = []
                values = []
                
                for key, value in db_data.items():
                    fields.append(key)
                    placeholders.append('?')
                    values.append(value)
                
                # 构建SQL
                sql = f"INSERT INTO {self.table} ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
                
                # 执行SQL
                self.db.execute(sql, tuple(values))
                self.db.commit()
            else:
                # 更新现有记录
                ticker_indicator = TickerIndicatorUpdate(**{
                    'time_key': time_key,
                    'history': entity.get('history'),
                    'status': entity.get('status')
                })
                db_data = ticker_indicator_to_dict(ticker_indicator)
                
                # 排除不更新的字段
                exclude_keys = ['id', 'code', 'version', 'create_time', 'creator', 'mender']
                for key in exclude_keys:
                    if key in db_data:
                        del db_data[key]
                
                # 过滤None值
                filtered_data = {k: v for k, v in db_data.items() if v is not None}
                
                if not filtered_data:
                    return
                
                # 构建SQL参数和SET子句
                set_clauses = []
                values = []
                
                for key, value in filtered_data.items():
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
                
                # 添加条件参数
                values.extend([ticker_id, indicator_key, kl_type])
                
                # 构建SQL
                sql = f"UPDATE {self.table} SET {', '.join(set_clauses)} WHERE ticker_id = ? AND indicator_key = ? AND kl_type = ?"
                
                # 执行SQL
                self.db.execute(sql, tuple(values))
                self.db.commit()
                
        except Exception as e:
            logger.error(f"更新指标记录错误: {e}")
            self.db.rollback()

    def update_items(self, ticker_id: int, indicators: Dict[str, Dict[str, Any]], kl_type: str, time_key: str) -> None:
        """批量更新或创建指标记录

        Args:
            ticker_id: 股票ID
            indicators: 指标字典，键为指标键，值为指标数据
            kl_type: K线类型
            time_key: 时间键

        Returns:
            None
        """
        try:
            for indicator_key, entity in indicators.items():
                self.update_item(ticker_id, indicator_key, kl_type, time_key, entity)
        except Exception as e:
            logger.error(f"批量更新指标记录错误: {e}")
            self.db.rollback()
