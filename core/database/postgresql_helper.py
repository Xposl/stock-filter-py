#!/usr/bin/env python3

import os
from typing import Any, Dict, List, Optional, Union, cast

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row
from sqlalchemy import create_engine

load_dotenv()


class PostgresqlHelper:
    """
    PostgreSQL数据库助手类
    支持:name格式参数和标准参数格式
    """

    def __init__(self):
        self.host = os.getenv("DB_HOST")
        self.port = os.getenv("DB_PORT")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.database = os.getenv("DB_NAME")

        self.conn = psycopg.connect(
            host=self.host,
            port=self.port,
            dbname=self.database,
            user=self.user,
            password=self.password,
            row_factory=dict_row,  # type: ignore
        )
        self.cursor = self.conn.cursor()

    def _convert_params(self, sql: str, params: Optional[Union[dict, tuple]]) -> tuple:
        """
        转换:name格式参数为psycopg3格式

        Args:
            sql: SQL语句
            params: 参数（字典或元组）

        Returns:
            (转换后的SQL, 转换后的参数)
        """
        if not params:
            return sql, params

        if isinstance(params, dict):
            # 字典参数：将:name转换为%(name)s (psycopg3仍然支持这种格式)
            converted_sql = sql
            # 按参数名长度倒序排列，避免短参数名匹配长参数名的问题
            sorted_keys = sorted(params.keys(), key=len, reverse=True)
            for key in sorted_keys:
                converted_sql = converted_sql.replace(f":{key}", f"%({key})s")
            return converted_sql, params
        else:
            # 元组参数：保持原样
            return sql, params

    def execute(self, sql: str, params: Optional[Union[dict, tuple]] = None) -> None:
        """
        执行SQL语句

        Args:
            sql: SQL语句
            params: SQL参数
        """
        if not self.cursor or not self.conn:
            raise RuntimeError("数据库连接未建立")
            
        try:
            converted_sql, converted_params = self._convert_params(sql, params)
            self.cursor.execute(converted_sql, converted_params)
        except Exception as e:
            self.conn.rollback()  # 错误时回滚
            raise e

    def commit(self) -> None:
        """提交事务"""
        if self.conn:
            self.conn.commit()

    def rollback(self) -> None:
        """回滚事务"""
        if self.conn:
            self.conn.rollback()

    def get_sqlalchemy_engine(self):
        """获取SQLAlchemy引擎"""
        return create_engine(
            f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        )

    def query(self, sql: str, params: Optional[Union[dict, tuple]] = None) -> list[dict]:
        """
        查询数据

        Args:
            sql: SQL查询语句
            params: SQL参数

        Returns:
            查询结果列表
        """
        if not self.cursor:
            raise RuntimeError("数据库连接未建立")
            
        converted_sql, converted_params = self._convert_params(sql, params)
        self.cursor.execute(converted_sql, converted_params)
        rows = self.cursor.fetchall()
        # psycopg3 with dict_row already returns dict objects
        return cast(List[Dict[str, Any]], rows)

    def query_one(self, sql: str, params: Optional[Union[dict, tuple]] = None) -> Optional[dict]:
        """
        查询单条数据

        Args:
            sql: SQL查询语句
            params: SQL参数

        Returns:
            单条查询结果
        """
        if not self.cursor:
            raise RuntimeError("数据库连接未建立")
            
        converted_sql, converted_params = self._convert_params(sql, params)
        self.cursor.execute(converted_sql, converted_params)
        row = self.cursor.fetchone()
        # psycopg3 with dict_row already returns dict objects
        return cast(Optional[Dict[str, Any]], row)

    def close(self):
        """安全关闭数据库连接"""
        try:
            if hasattr(self, "cursor") and self.cursor:
                self.cursor.close()
            if hasattr(self, "conn") and self.conn:
                self.conn.close()
        except Exception:
            pass
        finally:
            self.cursor = None
            self.conn = None

    def __del__(self):
        self.close()
