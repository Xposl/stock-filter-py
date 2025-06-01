#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from typing import Optional, List, Dict, Any, Tuple, Union
from sqlite3 import Connection, Cursor

class SqliteHelper:
    """
    SQLite数据库助手类
    支持:name格式参数和标准参数格式
    """
    
    def __init__(self, db_path: str = 'investnote.db'):
        """
        初始化SQLite数据库连接
        
        Args:
            db_path: SQLite数据库文件路径
        """
        self.db_path = db_path
        self.conn: Optional[Connection] = None
        self.cursor: Optional[Cursor] = None
        self._connect()
    
    def _connect(self) -> None:
        """
        建立SQLite数据库连接
        """
        try:
            self.conn = sqlite3.connect(self.db_path, timeout=10)
            # 启用外键约束
            self.conn.execute("PRAGMA foreign_keys = ON")
            # 配置返回字典形式的结果
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
        except Exception as e:
            print(f"数据库连接错误: {e}")
            raise e
    
    def _convert_params(self, sql: str, params: Union[Dict, Tuple]) -> tuple:
        """
        转换参数格式以适配SQLite
        
        Args:
            sql: SQL语句
            params: 参数（字典或元组）
            
        Returns:
            (转换后的SQL, 转换后的参数)
        """
        if not params:
            return sql, params
            
        if isinstance(params, dict):
            # 字典参数：SQLite原生支持:name格式，保持原样
            return sql, params
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
            if converted_params:
                self.cursor.execute(converted_sql, converted_params)
            else:
                self.cursor.execute(converted_sql)
        except Exception as e:
            self.conn.rollback()
            print(f"SQL执行错误: {e}")
            print(f"SQL: {sql}")
            print(f"参数: {params}")
            raise e
    
    def execute_many(self, sql: str, params_list: List[Union[Dict, Tuple]]) -> None:
        """
        批量执行SQL语句
        
        Args:
            sql: SQL语句
            params_list: SQL参数列表
        """
        try:
            self.cursor.executemany(sql, params_list)
        except Exception as e:
            self.conn.rollback()
            print(f"批量SQL执行错误: {e}")
            raise e
    
    def query(self, sql: str, params: Union[Dict, Tuple] = None) -> List[Dict[str, Any]]:
        """
        查询数据
        
        Args:
            sql: SQL查询语句
            params: SQL参数
            
        Returns:
            查询结果列表，每个元素为字典
        """
        try:
            converted_sql, converted_params = self._convert_params(sql, params)
            if converted_params:
                self.cursor.execute(converted_sql, converted_params)
            else:
                self.cursor.execute(converted_sql)
            
            rows = self.cursor.fetchall()
            # 将 sqlite3.Row 对象转换为字典列表
            result = [dict(row) for row in rows]
            return result
        except Exception as e:
            print(f"查询错误: {e}")
            raise e
    
    def query_one(self, sql: str, params: Union[Dict, Tuple] = None) -> Optional[Dict[str, Any]]:
        """
        查询单条数据
        
        Args:
            sql: SQL查询语句
            params: SQL参数
            
        Returns:
            单条查询结果，为字典或None
        """
        try:
            converted_sql, converted_params = self._convert_params(sql, params)
            if converted_params:
                self.cursor.execute(converted_sql, converted_params)
            else:
                self.cursor.execute(converted_sql)
            
            row = self.cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            print(f"查询错误: {e}")
            raise e
    
    def commit(self) -> None:
        """
        提交事务
        """
        if self.conn:
            self.conn.commit()
    
    def rollback(self) -> None:
        """
        回滚事务
        """
        if self.conn:
            self.conn.rollback()
    
    def close(self) -> None:
        """
        关闭数据库连接
        """
        try:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
        except Exception as e:
            print(f"关闭连接错误: {e}")
        finally:
            self.cursor = None
            self.conn = None
    
    def __del__(self) -> None:
        """
        析构函数，确保连接关闭
        """
        self.close()
