#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from core.DB.DBAdapter import DBAdapter
import os

def main():
    """
    数据库操作示例演示
    """
    print("===== SQLite数据库操作示例 =====")
    
    # 确保使用SQLite
    os.environ['DB_TYPE'] = 'sqlite'
    os.environ['SQLITE_DB_PATH'] = 'investnote.db'
    
    # 初始化数据库连接
    db = DBAdapter()
    
    try:
        # 示例1: 查询所有表
        print("\n1. 查询数据库中的所有表:")
        tables = db.query("SELECT name FROM sqlite_master WHERE type='table';")
        for table in tables:
            print(f"  - {table['name']}")
        
        # 示例2: 查询示例数据
        print("\n2. 查询项目策略统计数据:")
        result = db.query("""
            SELECT
                s.name AS strategy_name,
                ps.net_profit,
                ps.gross_profit,
                ps.gross_loss,
                ps.trades,
                ps.win_trades,
                ps.loss_trades,
                ROUND((ps.win_trades * 100.0 / ps.trades), 2) AS win_rate
            FROM project_strategy ps
            JOIN strategy s ON ps.strategy_id = s.id
            ORDER BY ps.net_profit DESC;
        """)
        
        print("\n策略统计数据:")
        print("%-15s %-12s %-12s %-12s %-8s %-10s %-10s %-8s" % 
              ("策略名称", "净利润", "总利润", "总亏损", "交易次数", "盈利次数", "亏损次数", "胜率(%)"))
        print("-" * 90)
        
        for row in result:
            print("%-15s %-12.2f %-12.2f %-12.2f %-8d %-10d %-10d %-8.2f" % (
                row['strategy_name'], 
                row['net_profit'],
                row['gross_profit'],
                row['gross_loss'],
                row['trades'],
                row['win_trades'],
                row['loss_trades'],
                row['win_rate']
            ))
        
        # 示例3: 插入新数据
        print("\n3. 插入新的股票数据:")
        
        # 检查股票是否已存在
        ticker_exists = db.query_one("SELECT id FROM ticker WHERE code = 'GOOG';")
        
        if not ticker_exists:
            # 插入新股票
            db.execute("""
                INSERT INTO ticker (code, name, group_id) 
                VALUES ('GOOG', '谷歌', 1);
            """)
            db.commit()
            print(f"  - 已插入新股票: GOOG (谷歌)")
        else:
            print(f"  - 股票 GOOG 已存在，跳过插入")
        
        # 示例4: 复杂查询 - 获取项目中的所有股票
        print("\n4. 查询项目中的所有股票:")
        project_tickers = db.query("""
            SELECT 
                p.name AS project_name,
                t.code AS ticker_code,
                t.name AS ticker_name
            FROM project p
            JOIN project_ticker pt ON p.id = pt.project_id
            JOIN ticker t ON pt.ticker_id = t.id
            WHERE p.is_deleted = 0 AND t.is_deleted = 0
            ORDER BY p.name, t.code;
        """)
        
        for row in project_tickers:
            print(f"  - 项目: {row['project_name']}, 股票: {row['ticker_code']} ({row['ticker_name']})")
        
        # 示例5: 使用事务进行多步操作
        print("\n5. 使用事务进行多步操作:")
        try:
            # 开始事务
            # 创建新项目
            db.execute("""
                INSERT INTO project (name, description) 
                VALUES ('科技股投资组合', '专注于科技领域股票的投资组合');
            """)
            
            # 获取新项目ID
            new_project = db.query_one("SELECT id FROM project WHERE name = '科技股投资组合';")
            new_project_id = new_project['id']
            
            # 将谷歌股票添加到新项目
            google = db.query_one("SELECT id FROM ticker WHERE code = 'GOOG';")
            if google:
                db.execute("""
                    INSERT INTO project_ticker (project_id, ticker_id) 
                    VALUES (?, ?);
                """, (new_project_id, google['id']))
            
            # 提交事务
            db.commit()
            print("  - 事务操作成功：创建了新项目并添加了谷歌股票")
        except Exception as e:
            # 出错时回滚
            db.rollback()
            print(f"  - 事务操作失败: {e}")
        
    except Exception as e:
        print(f"操作失败: {e}")
    finally:
        # 关闭数据库连接
        db.close()
        print("\n===== 示例结束 =====")

if __name__ == "__main__":
    main()
