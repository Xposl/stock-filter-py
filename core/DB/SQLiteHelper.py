import os
import sqlite3
from typing import Optional, List, Dict, Any, Tuple
from sqlite3 import Connection, Cursor

class SQLiteHelper:
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
            self.conn = sqlite3.connect(self.db_path)
            # 启用外键约束
            self.conn.execute("PRAGMA foreign_keys = ON")
            # 配置返回字典形式的结果
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
        except Exception as e:
            print(f"数据库连接错误: {e}")
            raise e
    
    def execute(self, sql: str, params: Tuple = None) -> None:
        """
        执行SQL语句
        
        Args:
            sql: SQL语句
            params: SQL参数
        """
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
        except Exception as e:
            self.conn.rollback()
            print(f"SQL执行错误: {e}")
            print(f"SQL: {sql}")
            print(f"参数: {params}")
            raise e
    
    def execute_many(self, sql: str, params_list: List[Tuple]) -> None:
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
    
    def query(self, sql: str, params: Tuple = None) -> List[Dict[str, Any]]:
        """
        查询数据
        
        Args:
            sql: SQL查询语句
            params: SQL参数
            
        Returns:
            查询结果列表，每个元素为字典
        """
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
            
            rows = self.cursor.fetchall()
            # 将 sqlite3.Row 对象转换为字典列表
            result = [dict(row) for row in rows]
            return result
        except Exception as e:
            print(f"查询错误: {e}")
            raise e
    
    def query_one(self, sql: str, params: Tuple = None) -> Optional[Dict[str, Any]]:
        """
        查询单条数据
        
        Args:
            sql: SQL查询语句
            params: SQL参数
            
        Returns:
            单条查询结果，为字典或None
        """
        try:
            if params:
                self.cursor.execute(sql, params)
            else:
                self.cursor.execute(sql)
            
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
    
    def create_tables(self) -> None:
        """
        创建数据库表
        """
        # 创建股票表
        self.execute('''
        CREATE TABLE IF NOT EXISTS ticker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            group_id INTEGER DEFAULT 0,
            type INTEGER DEFAULT 1,
            source INTEGER DEFAULT 1,
            status INTEGER DEFAULT 1,
            is_deleted INTEGER DEFAULT 0,
            time_key TEXT,
            open REAL,
            close REAL,
            high REAL,
            low REAL,
            volume REAL,
            turnover REAL,
            turnover_rate REAL,
            update_date TEXT,
            listed_date TEXT,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            version INTEGER DEFAULT 1
        )
        ''')
        
        # 创建策略表
        self.execute('''
        CREATE TABLE IF NOT EXISTS strategy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            strategy_key TEXT NOT NULL UNIQUE,
            is_deleted INTEGER DEFAULT 0,
            status INTEGER DEFAULT 1,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            version INTEGER DEFAULT 1
        )
        ''')
        
        # 创建项目表
        self.execute('''
        CREATE TABLE IF NOT EXISTS project (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            is_deleted INTEGER DEFAULT 0,
            status INTEGER DEFAULT 1,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            version INTEGER DEFAULT 1
        )
        ''')
        
        # 创建股票指标表
        self.execute('''
        CREATE TABLE IF NOT EXISTS ticker_indicator (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker_id INTEGER NOT NULL,
            indicator_id INTEGER NOT NULL,
            kl_type TEXT NOT NULL,
            value REAL,
            time_key TEXT NOT NULL,
            is_deleted INTEGER DEFAULT 0,
            status INTEGER DEFAULT 1,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticker_id) REFERENCES ticker (id),
            UNIQUE (ticker_id, indicator_id, kl_type, time_key)
        )
        ''')
        
        # 创建指标表
        self.execute('''
        CREATE TABLE IF NOT EXISTS indicator (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT NOT NULL UNIQUE,
            group_id INTEGER DEFAULT 0,
            is_deleted INTEGER DEFAULT 0,
            status INTEGER DEFAULT 1,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            version INTEGER DEFAULT 1
        )
        ''')
        
        # 创建估值表
        self.execute('''
        CREATE TABLE IF NOT EXISTS valuation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT NOT NULL UNIQUE,
            is_deleted INTEGER DEFAULT 0,
            status INTEGER DEFAULT 1,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            version INTEGER DEFAULT 1
        )
        ''')
        
        # 创建股票估值表
        self.execute('''
        CREATE TABLE IF NOT EXISTS ticker_valuation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker_id INTEGER NOT NULL,
            valuation_id INTEGER NOT NULL,
            value REAL,
            time_key TEXT NOT NULL,
            is_deleted INTEGER DEFAULT 0,
            status INTEGER DEFAULT 1,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticker_id) REFERENCES ticker (id),
            FOREIGN KEY (valuation_id) REFERENCES valuation (id),
            UNIQUE (ticker_id, valuation_id, time_key)
        )
        ''')
        
        # 创建股票策略表
        self.execute('''
        CREATE TABLE IF NOT EXISTS ticker_strategy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker_id INTEGER NOT NULL,
            strategy_id INTEGER NOT NULL,
            kl_type TEXT NOT NULL,
            signal INTEGER DEFAULT 0,
            price REAL,
            time_key TEXT NOT NULL,
            is_deleted INTEGER DEFAULT 0,
            status INTEGER DEFAULT 1,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticker_id) REFERENCES ticker (id),
            FOREIGN KEY (strategy_id) REFERENCES strategy (id),
            UNIQUE (ticker_id, strategy_id, kl_type, time_key)
        )
        ''')
        
        # 创建股票评分表
        self.execute('''
        CREATE TABLE IF NOT EXISTS ticker_score (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker_id INTEGER NOT NULL,
            score_type INTEGER NOT NULL,
            score REAL NOT NULL,
            time_key TEXT NOT NULL,
            is_deleted INTEGER DEFAULT 0,
            status INTEGER DEFAULT 1,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticker_id) REFERENCES ticker (id),
            UNIQUE (ticker_id, score_type, time_key)
        )
        ''')
        
        # 创建项目股票表
        self.execute('''
        CREATE TABLE IF NOT EXISTS project_ticker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            ticker_id INTEGER NOT NULL,
            is_deleted INTEGER DEFAULT 0,
            status INTEGER DEFAULT 1,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES project (id),
            FOREIGN KEY (ticker_id) REFERENCES ticker (id),
            UNIQUE (project_id, ticker_id)
        )
        ''')
        
        # 创建项目策略表
        self.execute('''
        CREATE TABLE IF NOT EXISTS project_strategy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            strategy_id INTEGER NOT NULL,
            net_profit REAL DEFAULT 0,
            gross_profit REAL DEFAULT 0,
            gross_loss REAL DEFAULT 0,
            trades INTEGER DEFAULT 0,
            win_trades INTEGER DEFAULT 0,
            loss_trades INTEGER DEFAULT 0,
            is_deleted INTEGER DEFAULT 0,
            status INTEGER DEFAULT 1,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES project (id),
            FOREIGN KEY (strategy_id) REFERENCES strategy (id),
            UNIQUE (project_id, strategy_id)
        )
        ''')
        
        # 创建K线数据表
        self.execute('''
        CREATE TABLE IF NOT EXISTS ticker_dayline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker_id INTEGER NOT NULL,
            time_key TEXT NOT NULL,
            open REAL,
            close REAL,
            high REAL,
            low REAL,
            volume REAL,
            turnover REAL,
            turnover_rate REAL,
            is_deleted INTEGER DEFAULT 0,
            status INTEGER DEFAULT 1,
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticker_id) REFERENCES ticker (id),
            UNIQUE (ticker_id, time_key)
        )
        ''')
        
        self.commit()
        print("数据库表创建成功！")
