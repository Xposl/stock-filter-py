#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
为 ticker 表添加缺失字段的脚本:
- pettm: 市盈率(TTM)
- pb: 市净率
- total_share: 总股本
- lot_size: 最小交易单位
"""

import os
import sys

# 将项目根目录添加到Python路径中
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

import sqlite3
from typing import Optional

def add_missing_columns(db_path: str = 'investnote.db') -> None:
    """
    为 ticker 表添加缺失的字段
    
    Args:
        db_path: 数据库文件路径
    """
    # 检查数据库文件是否存在
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在 {db_path}")
        sys.exit(1)
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查列是否已存在
        cursor.execute("PRAGMA table_info(ticker)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # 需要添加的列及其类型
        columns_to_add = {
            'pe_forecast': 'REAL',
            'pettm': 'REAL',
            'pb': 'REAL',
            'total_share': 'REAL',
            'lot_size': 'INTEGER DEFAULT 100',
            'modify_time': 'TEXT'
        }
        
        # 添加缺失的列
        for column_name, column_type in columns_to_add.items():
            if column_name in column_names:
                print(f"{column_name} 字段已存在于 ticker 表中")
            else:
                cursor.execute(f"ALTER TABLE ticker ADD COLUMN {column_name} {column_type}")
                print(f"成功添加 {column_name} 字段到 ticker 表")
        
        # 提交更改
        conn.commit()
        
        # 关闭连接
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)

def main() -> None:
    """
    主函数
    """
    # 默认数据库路径
    default_db_path = 'investnote.db'
    
    # 从命令行参数获取数据库路径 (如果有)
    db_path = sys.argv[1] if len(sys.argv) > 1 else default_db_path
    
    # 添加缺失的字段
    add_missing_columns(db_path)
    
    print("数据库修改完成！")

if __name__ == "__main__":
    main()
