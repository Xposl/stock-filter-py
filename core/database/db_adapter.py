#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from typing import Optional, Dict, List, Union, Tuple
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class DbAdapter:
    """
    数据库适配器，根据环境配置选择使用不同数据库
    统一使用:name参数格式，由底层helper处理具体数据库的参数转换
    """
    
    def __init__(self):
        """
        初始化数据库适配器
        """
        # 使用统一的DB_TYPE环境变量
        self.db_type = os.getenv('DB_TYPE', 'sqlite').lower()
        
        if self.db_type == 'postgres' or self.db_type == 'postgresql':
            # 使用PostgreSQL
            from .postgresql_helper import PostgresqlHelper
            self.db = PostgresqlHelper()
        elif self.db_type == 'mysql':
            # 使用MySQL
            from .mysql_helper import MysqlHelper
            self.db = MysqlHelper()
        else:
            # 使用SQLite
            from .sqlite_helper import SqliteHelper
            db_path = os.getenv('SQLITE_DB_PATH', 'investnote.db')
            self.db = SqliteHelper(db_path)
    
    def execute(self, sql: str, params: Union[Dict, Tuple] = None) -> None:
        """
        执行SQL语句
        
        Args:
            sql: SQL语句，使用:name格式参数
            params: SQL参数，字典或元组格式
        """
        self.db.execute(sql, params)
    
    def query(self, sql: str, params: Union[Dict, Tuple] = None) -> List[Dict]:
        """
        查询数据
        
        Args:
            sql: SQL查询语句，使用:name格式参数
            params: SQL参数，字典或元组格式
            
        Returns:
            查询结果列表，每个元素为字典
        """
        return self.db.query(sql, params)
    
    def query_one(self, sql: str, params: Union[Dict, Tuple] = None) -> Optional[Dict]:
        """
        查询单条数据
        
        Args:
            sql: SQL查询语句，使用:name格式参数
            params: SQL参数，字典或元组格式
            
        Returns:
            单条查询结果，为字典或None
        """
        return self.db.query_one(sql, params)
    
    def commit(self) -> None:
        """
        提交事务
        """
        self.db.commit()
    
    def rollback(self) -> None:
        """
        回滚事务
        """
        self.db.rollback()
    
    def close(self) -> None:
        """
        关闭数据库连接
        """
        self.db.close()
    
    def __del__(self) -> None:
        """
        析构函数，确保连接关闭
        """
        try:
            self.close()
        except Exception:
            pass
    
    @property
    def cursor(self):
        """
        获取底层游标
        
        Returns:
            数据库游标
        """
        return self.db.cursor
    
    @property
    def conn(self):
        """
        获取底层连接
        
        Returns:
            数据库连接
        """
        return self.db.conn
    
    def get_sqlalchemy_engine(self):
        """
        获取SQLAlchemy引擎
        
        Returns:
            SQLAlchemy引擎
        """
        if hasattr(self.db, 'get_sqlalchemy_engine'):
            return self.db.get_sqlalchemy_engine()
        else:
            # SQLite fallback
            import sqlalchemy
            return sqlalchemy.create_engine(f'sqlite:///{self.db.db_path}')
