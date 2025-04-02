#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from core.DB.SQLiteHelper import SQLiteHelper
from typing import Optional

def init_database(db_path: str = 'investnote.db') -> SQLiteHelper:
    """
    初始化SQLite数据库
    
    Args:
        db_path: 数据库文件路径
        
    Returns:
        SQLiteHelper 实例
    """
    # 检查数据库文件是否已存在
    db_exists = os.path.exists(db_path)
    
    # 创建SQLiteHelper实例
    db = SQLiteHelper(db_path)
    
    # 如果数据库文件不存在或表不存在，创建所有表
    if not db_exists:
        print(f"创建新的SQLite数据库: {db_path}")
        db.create_tables()
    else:
        print(f"使用现有SQLite数据库: {db_path}")
    
    return db

def test_database(db: SQLiteHelper) -> None:
    """
    测试数据库连接和表结构
    
    Args:
        db: SQLiteHelper 实例
    """
    try:
        # 测试表是否存在
        tables_result = db.query("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table['name'] for table in tables_result]
        
        print("数据库连接成功！")
        print(f"数据库包含以下表: {', '.join(tables)}")
        
        # 显示每个表的结构
        for table in tables:
            if table != 'sqlite_sequence':  # 跳过sqlite内部表
                schema_result = db.query(f"PRAGMA table_info({table});")
                columns = [f"{col['name']} ({col['type']})" for col in schema_result]
                print(f"\n表 '{table}' 的结构:")
                for col in columns:
                    print(f"  - {col}")
    except Exception as e:
        print(f"数据库测试失败: {e}")

def insert_sample_data(db: SQLiteHelper) -> None:
    """
    插入示例数据
    
    Args:
        db: SQLiteHelper 实例
    """
    try:
        # 检查是否已有数据
        existing_strategies = db.query("SELECT COUNT(*) as count FROM strategy;")
        if existing_strategies and existing_strategies[0]['count'] > 0:
            print("数据库已包含数据，跳过示例数据插入")
            return

        print("插入示例数据...")
        
        # 插入示例策略
        db.execute("INSERT INTO strategy (name, strategy_key) VALUES ('MACD策略', 'MACD_Strategy');")
        db.execute("INSERT INTO strategy (name, strategy_key) VALUES ('KDJ策略', 'KDJ_Strategy');")
        
        # 插入示例项目
        db.execute("INSERT INTO project (name, description) VALUES ('投资组合A', '大盘蓝筹股投资组合');")
        
        # 插入示例股票
        db.execute("INSERT INTO ticker (code, name) VALUES ('AAPL', '苹果公司');")
        db.execute("INSERT INTO ticker (code, name) VALUES ('MSFT', '微软公司');")
        
        # 插入项目与股票关联
        db.execute("INSERT INTO project_ticker (project_id, ticker_id) VALUES (1, 1);")
        db.execute("INSERT INTO project_ticker (project_id, ticker_id) VALUES (1, 2);")
        
        # 插入项目策略数据
        db.execute("""
        INSERT INTO project_strategy 
        (project_id, strategy_id, net_profit, gross_profit, gross_loss, trades, win_trades, loss_trades) 
        VALUES (1, 1, 5000, 8000, -3000, 20, 15, 5);
        """)
        
        db.execute("""
        INSERT INTO project_strategy 
        (project_id, strategy_id, net_profit, gross_profit, gross_loss, trades, win_trades, loss_trades) 
        VALUES (1, 2, 3000, 5000, -2000, 15, 10, 5);
        """)
        
        db.commit()
        print("示例数据插入成功！")
    except Exception as e:
        db.rollback()
        print(f"示例数据插入失败: {e}")

def main() -> None:
    """
    主函数
    """
    # 默认数据库路径
    default_db_path = 'investnote.db'
    
    # 从命令行参数获取数据库路径 (如果有)
    db_path = sys.argv[1] if len(sys.argv) > 1 else default_db_path
    
    # 初始化数据库
    db = init_database(db_path)
    
    # 测试数据库
    test_database(db)
    
    # 询问是否插入示例数据
    while True:
        choice = input("\n是否插入示例数据? (y/n): ").strip().lower()
        if choice in ('y', 'yes', '是', 'Y'):
            insert_sample_data(db)
            break
        elif choice in ('n', 'no', '否', 'N'):
            print("跳过示例数据插入")
            break
        else:
            print("无效输入，请输入 'y' 或 'n'")
    
    # 关闭数据库连接
    db.close()
    print("\nSQLite数据库初始化完成！")

if __name__ == "__main__":
    main()
