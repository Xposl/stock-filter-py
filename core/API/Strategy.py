#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from typing import Dict, Any, Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Strategy:
    """
    策略管理类
    """
    table = 'strategy'

    def __init__(self, db_connection):
        """
        初始化策略管理
        
        Args:
            db_connection: 数据库连接
        """
        self.db = db_connection

    def insertItem(self, key: str) -> Dict[str, Any]:
        """
        插入策略项
        
        Args:
            key: 策略键
            
        Returns:
            插入的策略记录
        """
        try:
            data = {
                'name': key[:-9],
                'strategy_key': key,
                'is_deleted': 0, 
                'status': 1
            }
            
            # 构建SQL参数和占位符
            fields = []
            placeholders = []
            values = []
            
            for field, value in data.items():
                fields.append(field)
                placeholders.append('?')
                values.append(value)
            
            # 构建SQL
            sql = f"INSERT INTO {self.table} ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
            
            # 执行SQL
            self.db.execute(sql, tuple(values))
            self.db.commit()
            
            return self.getItemByKey(key)
            
        except Exception as e:
            logger.error(f"插入策略错误: {e}")
            self.db.rollback()
            return None

    def getItemByKey(self, key: str) -> Optional[Dict[str, Any]]:
        """
        根据策略键获取策略
        
        Args:
            key: 策略键
            
        Returns:
            策略记录或None
        """
        try:
            sql = f"SELECT * FROM {self.table} WHERE strategy_key = ?"
            result = self.db.query_one(sql, (key,))
            
            if result is None:
                return self.insertItem(key)
            
            return result
            
        except Exception as e:
            logger.error(f"获取策略错误: {e}")
            return None
