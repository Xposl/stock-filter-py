#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

# 将项目根目录添加到Python路径中
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from core.DB.SQLiteHelper import SQLiteHelper

def clean_database(db_path: str = 'investnote.db') -> None:
    """
    清空数据库中的所有表数据
    
    Args:
        db_path: 数据库文件路径
    """
    # 检查数据库文件是否存在
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件 '{db_path}' 不存在!")
        return
    
    # 创建SQLiteHelper实例
    try:
        db = SQLiteHelper(db_path)
        print(f"成功连接到数据库: {db_path}")
        
        # 获取所有表名
        tables_result = db.query("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table['name'] for table in tables_result]
        
        if not tables:
            print("数据库中没有找到表")
            return
        
        # 禁用外键约束以避免删除顺序问题
        db.execute("PRAGMA foreign_keys = OFF;")
        
        # 删除每个表中的数据
        for table in tables:
            if table != 'sqlite_sequence':  # 跳过sqlite内部表
                try:
                    print(f"正在清空表 '{table}'...")
                    db.execute(f"DELETE FROM {table};")
                except Exception as e:
                    print(f"清空表 '{table}' 时出错: {e}")
        
        # 重置自增ID
        for table in tables:
            if table != 'sqlite_sequence':  # 除了sqlite_sequence表
                try:
                    db.execute(f"DELETE FROM sqlite_sequence WHERE name = '{table}';")
                except Exception as e:
                    print(f"重置表 '{table}' 的自增ID时出错: {e}")
        
        # 重新启用外键约束
        db.execute("PRAGMA foreign_keys = ON;")
        
        # 提交更改
        db.commit()
        print("所有表数据已清空!")
        
    except Exception as e:
        print(f"清空数据库时发生错误: {e}")
    finally:
        # 关闭数据库连接
        if 'db' in locals():
            db.close()

def main() -> None:
    """
    主函数
    """
    # 默认数据库路径
    default_db_path = 'investnote.db'
    
    # 从命令行参数获取数据库路径 (如果有)
    db_path = sys.argv[1] if len(sys.argv) > 1 else default_db_path
    
    # 确认操作
    print(f"警告: 即将清空数据库 '{db_path}' 中的所有数据！")
    while True:
        choice = input("确定要继续操作吗? (y/n): ").strip().lower()
        if choice in ('y', 'yes', '是', 'Y'):
            clean_database(db_path)
            break
        elif choice in ('n', 'no', '否', 'N'):
            print("操作已取消")
            break
        else:
            print("无效输入，请输入 'y' 或 'n'")

if __name__ == "__main__":
    main()
