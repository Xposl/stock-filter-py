#!/usr/bin/env python3
"""
安全的Repository基类
提供安全的SQL查询方法，防止SQL注入
"""

import re
from typing import Union, Optional, Dict, List, Any
from core.database.db_adapter import DbAdapter


class BaseRepository:
    """
    安全的Repository基类
    
    提供安全的SQL查询方法，防止SQL注入攻击：
    1. 表名白名单验证
    2. 参数化查询
    3. SQL注入防护
    """
    
    # 允许的表名白名单（需要子类重写）
    ALLOWED_TABLES: List[str] = []
    
    def __init__(self, db: DbAdapter, table: str):
        """
        初始化Repository
        
        Args:
            db: 数据库适配器
            table: 表名
            
        Raises:
            ValueError: 当表名不在白名单中时
        """
        self.db = db
        self._validate_table_name(table)
        self.table = table
    
    def _validate_table_name(self, table: str) -> None:
        """
        验证表名是否安全
        
        Args:
            table: 表名
            
        Raises:
            ValueError: 当表名不安全时
        """
        # 检查表名是否在白名单中
        if self.ALLOWED_TABLES and table not in self.ALLOWED_TABLES:
            raise ValueError(f"表名 '{table}' 不在允许的白名单中")
        
        # 检查表名格式（只允许字母、数字、下划线）
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table):
            raise ValueError(f"表名 '{table}' 包含不安全字符")
        
        # 防止表名过长
        if len(table) > 64:
            raise ValueError(f"表名 '{table}' 长度超出限制")
    
    def _build_safe_sql(self, base_sql: str, table_placeholder: str = "TABLE_NAME") -> str:
        """
        构建安全的SQL语句，使用预验证的表名
        
        Args:
            base_sql: 基础SQL模板，使用TABLE_NAME作为表名占位符
            table_placeholder: 表名占位符
            
        Returns:
            安全的SQL语句
        """
        return base_sql.replace(table_placeholder, self.table)
    
    def safe_query(self, sql_template: str, params: Union[dict, tuple] = None) -> List[Dict[str, Any]]:
        """
        安全查询方法
        
        Args:
            sql_template: SQL模板，使用TABLE_NAME作为表名占位符
            params: 查询参数
            
        Returns:
            查询结果列表
        """
        safe_sql = self._build_safe_sql(sql_template)
        return self.db.query(safe_sql, params)
    
    def safe_query_one(self, sql_template: str, params: Union[dict, tuple] = None) -> Optional[Dict[str, Any]]:
        """
        安全单条查询方法
        
        Args:
            sql_template: SQL模板，使用TABLE_NAME作为表名占位符
            params: 查询参数
            
        Returns:
            单条查询结果或None
        """
        safe_sql = self._build_safe_sql(sql_template)
        return self.db.query_one(safe_sql, params)
    
    def safe_execute(self, sql_template: str, params: Union[dict, tuple] = None) -> None:
        """
        安全执行方法
        
        Args:
            sql_template: SQL模板，使用TABLE_NAME作为表名占位符
            params: 执行参数
        """
        safe_sql = self._build_safe_sql(sql_template)
        self.db.execute(safe_sql, params)
    
    def get_by_id(self, entity_id: Union[int, str]) -> Optional[Dict[str, Any]]:
        """
        根据ID获取实体（通用方法）
        
        Args:
            entity_id: 实体ID
            
        Returns:
            实体数据或None
        """
        sql_template = "SELECT * FROM TABLE_NAME WHERE id = :id"
        return self.safe_query_one(sql_template, {"id": entity_id})
    
    def get_all(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取所有记录（通用方法）
        
        Args:
            limit: 限制条数
            
        Returns:
            记录列表
        """
        if limit:
            sql_template = "SELECT * FROM TABLE_NAME LIMIT :limit"
            return self.safe_query(sql_template, {"limit": limit})
        else:
            sql_template = "SELECT * FROM TABLE_NAME"
            return self.safe_query(sql_template)
    
    def delete_by_id(self, entity_id: Union[int, str]) -> None:
        """
        根据ID删除实体（通用方法）
        
        Args:
            entity_id: 实体ID
        """
        sql_template = "DELETE FROM TABLE_NAME WHERE id = :id"
        self.safe_execute(sql_template, {"id": entity_id})
    
    def count(self) -> int:
        """
        统计记录数（通用方法）
        
        Returns:
            记录总数
        """
        sql_template = "SELECT COUNT(*) as count FROM TABLE_NAME"
        result = self.safe_query_one(sql_template)
        return result["count"] if result else 0
