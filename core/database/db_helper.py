#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine
import psycopg2
import os
from dotenv import load_dotenv 
from typing import Optional, List, Dict

load_dotenv()

class DbHelper:
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

    def execute(self, sql: str, params=None) -> None:
        try:
            self.cursor.execute(sql, params)
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
        return create_engine(
            f'postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}'
        )

    def query(self, sql: str, params=None) -> List[Dict]:
        self.cursor.execute(sql, params)
        return self.cursor.fetchall()

    def query_one(self, sql: str, params=None) -> Optional[Dict]:
        self.cursor.execute(sql, params)
        return self.cursor.fetchone()

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
