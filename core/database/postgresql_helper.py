#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
import psycopg2
import psycopg2.extras
import os
from dotenv import load_dotenv 
from typing import Optional, List, Dict, Union, Tuple

load_dotenv()

class PostgresqlHelper:
    """
    PostgreSQL数据库助手类
    支持:name格式参数和标准参数格式
    """
    
    def __init__(self):
        self.host = os.getenv('DB_HOST')
        self.port = os.getenv('DB_PORT')
        self.user = os.getenv('DB_USER')
        self.password = os.getenv('DB_PASSWORD')
        self.database = os.getenv('DB_NAME')
        
        self.conn = psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password
        )
        self.cursor = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def _convert_params(self, sql: str, params: Union[Dict, Tuple]) -> tuple:
        """
        转换:name格式参数为PostgreSQL格式
        
        Args:
            sql: SQL语句
            params: 参数（字典或元组）
            
        Returns:
            (转换后的SQL, 转换后的参数)
        """
        if not params:
            return sql, params
            
        if isinstance(params, dict):
            # 字典参数：将:name转换为%(name)s
            converted_sql = sql
            # 按参数名长度倒序排列，避免短参数名匹配长参数名的问题
            sorted_keys = sorted(params.keys(), key=len, reverse=True)
            for key in sorted_keys:
                converted_sql = converted_sql.replace(f':{key}', f'%({key})s')
            return converted_sql, params
        else:
            # 元组参数：保持原样
            return sql, params

    def execute(self, sql: str, params: Union[Dict, Tuple] = None) -> None:
        """
        执行SQL语句
        
        Args:
            sql: SQL语句
            params: SQL参数
        """
        try:
            converted_sql, converted_params = self._convert_params(sql, params)
            self.cursor.execute(converted_sql, converted_params)
        except Exception as e:
            self.conn.rollback()  # 错误时回滚
            raise e

    def commit(self) -> None:
        """提交事务"""
        self.conn.commit()

    def rollback(self) -> None:
        """回滚事务"""
        self.conn.rollback()

    def get_sqlalchemy_engine(self):
        """获取SQLAlchemy引擎"""
        return create_engine(
            f'postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}'
        )

    def query(self, sql: str, params: Union[Dict, Tuple] = None) -> List[Dict]:
        """
        查询数据
        
        Args:
            sql: SQL查询语句
            params: SQL参数
            
        Returns:
            查询结果列表
        """
        converted_sql, converted_params = self._convert_params(sql, params)
        self.cursor.execute(converted_sql, converted_params)
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    def query_one(self, sql: str, params: Union[Dict, Tuple] = None) -> Optional[Dict]:
        """
        查询单条数据
        
        Args:
            sql: SQL查询语句
            params: SQL参数
            
        Returns:
            单条查询结果
        """
        converted_sql, converted_params = self._convert_params(sql, params)
        self.cursor.execute(converted_sql, converted_params)
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def close(self):
        """安全关闭数据库连接"""
        try:
            if hasattr(self, 'cursor') and self.cursor:
                self.cursor.close()
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
        except Exception:
            pass
        finally:
            self.cursor = None
            self.conn = None

    def __del__(self):
        self.close()
