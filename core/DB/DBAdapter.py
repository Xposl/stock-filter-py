#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from typing import Optional, Union, Dict, List, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class DBAdapter:
    """
    数据库适配器，可以根据环境配置选择使用PostgreSQL或SQLite
    """
    
    def __init__(self):
        """
        初始化数据库适配器
        """
        # 默认使用SQLite，除非环境变量明确指定使用PostgreSQL
        db_type = os.getenv('DB_TYPE', 'sqlite').lower()
        
        if db_type == 'postgres' or db_type == 'postgresql':
            # 使用PostgreSQL
            from .DBHelper import DBHelper
            self.db = DBHelper()
        else:
            # 使用SQLite
            from .SQLiteHelper import SQLiteHelper
            db_path = os.getenv('SQLITE_DB_PATH', 'investnote.db')
            self.db = SQLiteHelper(db_path)
    
    def execute(self, sql: str, params=None) -> None:
        """
        执行SQL语句
        
        Args:
            sql: SQL语句
            params: SQL参数
        """
        self.db.execute(sql, params)
    
    def query(self, sql: str, params=None) -> List[Dict]:
        """
        查询数据
        
        Args:
            sql: SQL查询语句
            params: SQL参数
            
        Returns:
            查询结果列表，每个元素为字典
        """
        return self.db.query(sql, params)
    
    def query_one(self, sql: str, params=None) -> Optional[Dict]:
        """
        查询单条数据
        
        Args:
            sql: SQL查询语句
            params: SQL参数
            
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
        self.close()
    
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
            SQLAlchemy引擎或None(如果不支持)
        """
        if hasattr(self.db, 'get_sqlalchemy_engine'):
            return self.db.get_sqlalchemy_engine()
        else:
            import sqlalchemy
            return sqlalchemy.create_engine(f'sqlite:///{self.db.db_path}')
