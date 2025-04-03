#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import copy
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from core.database.db_adapter import DbAdapter
from core.models.ticker import Ticker, TickerCreate, TickerUpdate, ticker_to_dict, dict_to_ticker
from core.enum.ticker_group import get_group_id_by_code

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TickerRepository:
    """
    使用Pydantic模型的Ticker仓库类
    """
    table = 'ticker'

    def __init__(self, db_connection: Optional[Any] = None):
        """
        初始化Ticker仓库
        
        Args:
            db_connection: 可选的数据库连接，如果未提供将使用DbAdapter创建新连接
        """
        if db_connection:
            self.db = db_connection
        else:
            self.db = DbAdapter()
    
    def get_by_code(self, code: str) -> Optional[Ticker]:
        """
        根据股票代码获取股票信息
        
        Args:
            code: 股票代码
            
        Returns:
            Ticker对象或None
        """
        try:
            sql = f"SELECT * FROM {self.table} WHERE code = ?"
            result = self.db.query_one(sql, (code,))
            if result:
                return dict_to_ticker(result)
            return None
        except Exception as e:
            logger.error(f"获取股票信息错误: {e}")
            return None
    
    def get_like_code(self, code: str) -> Optional[Ticker]:
        """
        根据股票代码模糊查询股票信息
        
        Args:
            code: 股票代码片段
            
        Returns:
            Ticker对象或None
        """
        try:
            sql = f"SELECT * FROM {self.table} WHERE code LIKE ?"
            result = self.db.query_one(sql, (f'%{code}%',))
            if result:
                return dict_to_ticker(result)
            return None
        except Exception as e:
            logger.error(f"模糊查询股票信息错误: {e}")
            return None
    
    def get_all(self) -> List[Ticker]:
        """
        获取所有股票信息
        
        Returns:
            Ticker对象列表
        """
        try:
            sql = f"SELECT * FROM {self.table}"
            results = self.db.query(sql)
            return [dict_to_ticker(result) for result in results]
        except Exception as e:
            logger.error(f"获取所有股票信息错误: {e}")
            return []
    
    def get_all_map(self) -> Dict[str, Ticker]:
        """
        获取所有股票信息，以代码为键的字典
        
        Returns:
            {股票代码: Ticker对象}形式的字典
        """
        try:
            tickers = self.get_all()
            return {ticker.code: ticker for ticker in tickers}
        except Exception as e:
            logger.error(f"获取股票信息映射错误: {e}")
            return {}
    
    def get_all_available(self, end_date: Optional[str] = None) -> List[Ticker]:
        """
        获取所有可用股票信息
        
        Args:
            end_date: 可选的结束日期
            
        Returns:
            可用的Ticker对象列表
        """
        try:
            if end_date is None:
                sql = f"SELECT * FROM {self.table} WHERE is_deleted = 0 AND status = 1 ORDER BY group_id"
                results = self.db.query(sql)
            else:
                sql = f"""
                    SELECT * FROM {self.table} 
                    WHERE is_deleted = 0 
                    AND (listed_date < ? OR listed_date IS NULL) 
                    AND status = 1 
                    ORDER BY group_id
                """
                results = self.db.query(sql, (end_date,))
            return [dict_to_ticker(result) for result in results]
        except Exception as e:
            logger.error(f"获取可用股票信息错误: {e}")
            return []
    
    def get_all_available_start_with(self, start_key: str) -> List[Ticker]:
        """
        获取以指定字符串开头的所有可用股票信息
        
        Args:
            start_key: 股票代码开头字符串
            
        Returns:
            Ticker对象列表
        """
        try:
            sql = f"""
                SELECT * FROM {self.table} 
                WHERE is_deleted = 0 
                AND code LIKE ? 
                AND status = 1
            """
            results = self.db.query(sql, (f'{start_key}%',))
            return [dict_to_ticker(result) for result in results]
        except Exception as e:
            logger.error(f"获取指定前缀股票信息错误: {e}")
            return []
    
    def get_update_time_by_code(self, code: str, kl_type: str) -> Optional[datetime]:
        """
        获取股票更新时间
        
        Args:
            code: 股票代码
            kl_type: K线类型
            
        Returns:
            更新时间或None
        """
        try:
            # SQLite和PostgreSQL的SQL语法有差异，这里使用兼容的写法
            sql = f"""
                SELECT 
                    CASE 
                        WHEN MIN(ts.time_key) < t.update_date AND MIN(ts.time_key) IS NOT NULL AND t.update_date IS NOT NULL THEN
                            CASE 
                                WHEN MIN(ts.time_key) < MIN(ti.time_key) AND MIN(ti.time_key) IS NOT NULL THEN MIN(ts.time_key)
                                ELSE MIN(ti.time_key) 
                            END
                        ELSE t.update_date
                    END AS update_time
                FROM {self.table} AS t 
                LEFT JOIN ticker_strategy AS ts ON ts.ticker_id = t.id AND ts.kl_type = ?
                LEFT JOIN ticker_indicator AS ti ON ti.ticker_id = t.id AND ti.kl_type = ?
                WHERE t.code = ?
            """
            result = self.db.query_one(sql, (kl_type, kl_type, code))
            if result and result['update_time']:
                # 尝试解析日期时间字符串
                if isinstance(result['update_time'], str):
                    try:
                        return datetime.fromisoformat(result['update_time'].replace('Z', '+00:00'))
                    except ValueError:
                        return datetime.strptime(result['update_time'], '%Y-%m-%d %H:%M:%S')
                else:
                    return result['update_time']
            return None
        except Exception as e:
            logger.error(f"获取更新时间错误: {e}")
            return None
    
    def create(self, code: str, name: str, data: Union[Dict, TickerCreate], commit: bool = True) -> Optional[Ticker]:
        """
        创建新的股票记录
        
        Args:
            code: 股票代码
            name: 股票名称
            data: 股票数据，可以是字典或TickerCreate对象
            commit: 是否立即提交事务
            
        Returns:
            创建的Ticker对象或None
        """
        try:
            # 转换为字典
            if isinstance(data, TickerCreate):
                entity = ticker_to_dict(data)
            else:
                entity = copy.copy(data)
            
            # 设置基本属性
            entity['name'] = name
            entity['group_id'] = get_group_id_by_code(code)
            entity['code'] = code
            entity['is_deleted'] = entity.get('is_deleted', 0)
            entity['status'] = entity.get('status', 1)
            
            # 处理枚举类型
            if 'type' in entity and hasattr(entity['type'], 'value'):
                entity['type'] = entity['type'].value
                
            # 添加创建时间和版本
            if 'create_time' not in entity:
                entity['create_time'] = datetime.now()
            if 'version' not in entity:
                entity['version'] = 1
            
            # 构建SQL参数和占位符
            fields = []
            placeholders = []
            values = []
            
            for key, value in entity.items():
                fields.append(key)
                placeholders.append('?')
                
                # 处理布尔值
                if isinstance(value, bool):
                    values.append(1 if value else 0)
                # 处理其他可能的枚举类型
                elif hasattr(value, 'value'):
                    values.append(value.value)
                else:
                    values.append(value)
            
            # 构建SQL
            sql = f"INSERT INTO {self.table} ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
            
            # 执行SQL
            self.db.execute(sql, tuple(values))
            
            # 提交事务
            if commit:
                self.db.commit()
            
            # 获取创建的记录
            return self.get_by_code(code)
        
        except Exception as e:
            logger.error(f"创建股票记录错误: {e}")
            if commit:
                self.db.rollback()
            return None
    
    def update(self, code: str, name: str, data: Union[Dict, TickerUpdate], commit: bool = True) -> Optional[Ticker]:
        """
        更新股票记录
        
        Args:
            code: 股票代码
            name: 股票名称
            data: 股票数据，可以是字典或TickerUpdate对象
            commit: 是否立即提交事务
            
        Returns:
            更新后的Ticker对象或None
        """
        try:
            # 转换为字典
            if isinstance(data, TickerUpdate):
                entity = ticker_to_dict(data)
            else:
                entity = copy.copy(data)
            
            # 设置基本属性
            entity['name'] = name
            entity['group_id'] = get_group_id_by_code(code)
            
            # 排除不需要更新的字段
            exclude_keys = ['id', 'code', 'version', 'create_time', 'creator', 'mender']
            for key in exclude_keys:
                if key in entity:
                    del entity[key]
            
            # 过滤None值
            filtered_entity = {k: v for k, v in entity.items() if v is not None}
            
            # 如果没有要更新的内容，直接返回
            if not filtered_entity:
                return self.get_by_code(code)
            
            # 处理枚举类型
            for key, value in list(filtered_entity.items()):
                if hasattr(value, 'value'):
                    filtered_entity[key] = value.value
            
            # 构建SQL参数和SET子句
            set_clauses = []
            values = []
            
            for key, value in filtered_entity.items():
                set_clauses.append(f"{key} = ?")
                
                # 处理布尔值
                if isinstance(value, bool):
                    values.append(1 if value else 0)
                # 处理其他可能的枚举类型
                elif hasattr(value, 'value'):
                    values.append(value.value)
                else:
                    values.append(value)
            
            # 添加代码参数
            values.append(code)
            
            # 构建SQL
            sql = f"UPDATE {self.table} SET {', '.join(set_clauses)} WHERE code = ?"
            
            # 执行SQL并提交
            self.db.execute(sql, tuple(values))
            # 提交事务
            if commit:
                self.db.commit()
            
            # 获取更新后的记录
            return self.get_by_code(code)
            
        except Exception as e:
            logger.error(f"更新股票记录错误: {e}")
            self.db.rollback()
            return None
    
    def update_or_create(self, code: str, name: str, data: Union[Dict, TickerCreate, TickerUpdate]) -> Optional[Ticker]:
        """
        更新或创建股票记录
        
        Args:
            code: 股票代码
            name: 股票名称
            data: 股票数据，可以是字典、TickerCreate或TickerUpdate对象
            
        Returns:
            Ticker对象或None
        """
        try:
            # 检查记录是否存在
            existing = self.get_by_code(code)
            
            if existing:
                return self.update(code, name, data)
            else:
                return self.create(code, name, data)
                
        except Exception as e:
            logger.error(f"更新或创建股票记录错误: {e}")
            self.db.rollback()
            return None
    
    def delete_by_id(self, id: int) -> bool:
        """
        删除股票记录
        
        Args:
            id: 股票ID
            
        Returns:
            是否成功删除
        """
        try:
            sql = f"DELETE FROM {self.table} WHERE id = ?"
            self.db.execute(sql, (id,))
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"删除股票记录错误: {e}")
            self.db.rollback()
            return False
