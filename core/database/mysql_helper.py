#!/usr/bin/env python3

import os
from typing import Any, Optional, Union

import pymysql
from dotenv import load_dotenv
from pymysql.cursors import DictCursor
from sqlalchemy import create_engine

load_dotenv()


class MysqlHelper:
    """
    MySQL数据库助手类
    支持:name格式参数和标准参数格式
    """

    def __init__(self):
        self.host = os.getenv("DB_HOST") or "localhost"
        self.port = int(os.getenv("DB_PORT", 3306))
        self.user = os.getenv("DB_USER") or ""
        self.password = os.getenv("DB_PASSWORD") or ""
        self.database = os.getenv("DB_NAME") or ""
        self.conn = pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            charset="utf8mb4",
            cursorclass=DictCursor,
        )
        self.cursor = self.conn.cursor()

    def _convert_params(self, sql: str, params: Optional[Union[dict, tuple]]) -> tuple:
        """
        转换:name格式参数为MySQL格式

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
        try:
            converted_sql, converted_params = self._convert_params(sql, params)
            if self.cursor:
                self.cursor.execute(converted_sql, converted_params)
        except Exception as e:
            if self.conn:
                self.conn.rollback()
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
            f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?charset=utf8mb4"
        )

    def query(
        self, sql: str, params: Optional[Union[dict, tuple]] = None
    ) -> list[dict[str, Any]]:
        """
        查询数据

        Args:
            sql: SQL查询语句
            params: SQL参数

        Returns:
            查询结果列表
        """
        converted_sql, converted_params = self._convert_params(sql, params)
        if self.cursor:
            self.cursor.execute(converted_sql, converted_params)
            result = self.cursor.fetchall()
            return list(result) if result else []
        return []

    def query_one(
        self, sql: str, params: Optional[Union[dict, tuple]] = None
    ) -> Optional[dict[str, Any]]:
        """
        查询单条数据

        Args:
            sql: SQL查询语句
            params: SQL参数

        Returns:
            单条查询结果
        """
        converted_sql, converted_params = self._convert_params(sql, params)
        if self.cursor:
            self.cursor.execute(converted_sql, converted_params)
            return self.cursor.fetchone()
        return None

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
            # 使用类型注释友好的方式设置为None
            if hasattr(self, "cursor"):
                self.cursor = None  # type: ignore
            if hasattr(self, "conn"):
                self.conn = None  # type: ignore

    def __del__(self):
        self.close()
