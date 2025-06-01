#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path
from typing import Optional

def get_database_url() -> str:
    """
    获取数据库连接URL
    
    支持多种数据库类型，根据环境变量自动选择：
    - SQLite（默认）: sqlite+aiosqlite:///path/to/database.db
    - PostgreSQL: postgresql+asyncpg://user:password@host:port/database
    - MySQL: mysql+aiomysql://user:password@host:port/database
    
    Returns:
        str: 数据库连接URL
    """
    # 从环境变量获取数据库配置，统一使用DB_*变量名
    database_type = os.getenv("DB_TYPE", "sqlite").lower()
    
    if database_type == "sqlite":
        # SQLite配置
        db_path = os.getenv("SQLITE_DB_PATH", "investnote.db")
        
        # 确保数据库文件路径是绝对路径
        if not os.path.isabs(db_path):
            # 如果是相对路径，则相对于项目根目录
            project_root = Path(__file__).parent.parent.parent
            db_path = str(project_root / db_path)
        
        # 确保数据库文件目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        return f"sqlite+aiosqlite:///{db_path}"
    
    elif database_type == "postgresql":
        # PostgreSQL配置
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        user = os.getenv("DB_USER", "investnote")
        password = os.getenv("DB_PASSWORD", "")
        database = os.getenv("DB_NAME", "investnote")
        
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
    
    elif database_type == "mysql":
        # MySQL配置
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "3306")
        user = os.getenv("DB_USER", "investnote")
        password = os.getenv("DB_PASSWORD", "")
        database = os.getenv("DB_NAME", "investnote")
        
        return f"mysql+aiomysql://{user}:{password}@{host}:{port}/{database}"
    
    else:
        raise ValueError(f"不支持的数据库类型: {database_type}")

def get_database_config() -> dict:
    """
    获取数据库配置信息
    
    Returns:
        dict: 数据库配置字典
    """
    database_type = os.getenv("DB_TYPE", "sqlite").lower()
    
    config = {
        "type": database_type,
        "url": get_database_url(),
        "echo": os.getenv("DB_ECHO", "false").lower() == "true",
        "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
    }
    
    if database_type == "sqlite":
        # SQLite特有配置
        config.update({
            "path": os.getenv("SQLITE_DB_PATH", "investnote.db"),
            "timeout": int(os.getenv("DB_TIMEOUT", "10")),
        })
    else:
        # PostgreSQL/MySQL共有配置
        config.update({
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432" if database_type == "postgresql" else "3306")),
            "user": os.getenv("DB_USER", "investnote"),
            "password": os.getenv("DB_PASSWORD", ""),
            "database": os.getenv("DB_NAME", "investnote"),
            "charset": os.getenv("DB_CHARSET", "utf8mb4"),
        })
    
    return config

def is_database_available() -> bool:
    """
    检查数据库是否可用
    
    Returns:
        bool: 数据库是否可用
    """
    try:
        database_url = get_database_url()
        database_type = os.getenv("DB_TYPE", "sqlite").lower()
        
        if database_type == "sqlite":
            # SQLite检查：确保文件路径有效
            db_path = database_url.replace("sqlite+aiosqlite:///", "")
            db_dir = os.path.dirname(db_path)
            return os.access(db_dir, os.W_OK) if db_dir else True
        else:
            # 对于其他数据库类型，需要实际连接测试
            # 这里简化处理，仅检查环境变量是否完整
            required_vars = ["DB_HOST", "DB_USER", "DB_NAME"]
            return all(os.getenv(var) for var in required_vars)
    
    except Exception:
        return False

# 导出主要函数
__all__ = [
    'get_database_url',
    'get_database_config', 
    'is_database_available'
] 