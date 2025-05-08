import os
from typing import Optional, List, Dict
from dotenv import load_dotenv
import pymysql
from sqlalchemy import create_engine

load_dotenv()

class MysqlHelper:
    def __init__(self):
        self.host = os.getenv('DB_HOST')
        self.port = int(os.getenv('DB_PORT', 3306))
        self.user = os.getenv('DB_USER')
        self.password = os.getenv('DB_PASSWORD')
        self.database = os.getenv('DB_NAME')
        self.conn = pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        self.cursor = self.conn.cursor()

    def execute(self, sql: str, params=None) -> None:
        try:
            self.cursor.execute(sql, params)
        except Exception as e:
            self.conn.rollback()
            raise e

    def commit(self) -> None:
        self.conn.commit()

    def rollback(self) -> None:
        self.conn.rollback()

    def get_sqlalchemy_engine(self):
        return create_engine(
            f'mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?charset=utf8mb4'
        )

    def query(self, sql: str, params=None) -> List[Dict]:
        self.cursor.execute(sql, params)
        return self.cursor.fetchall()

    def query_one(self, sql: str, params=None) -> Optional[Dict]:
        self.cursor.execute(sql, params)
        return self.cursor.fetchone()

    def close(self):
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