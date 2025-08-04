"""
数据库服务模块
包含基础设施功能：连接管理、会话管理、健康检查、Schema管理
移除所有业务相关逻辑，遵循分层架构原则
支持MySQL和PostgreSQL数据库
"""

import logging
import threading
import importlib

from contextlib import asynccontextmanager
from typing import Any, Optional, Dict, Type, List

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import get_settings

# 声明式基类
Base = declarative_base()

# 配置日志
logger = logging.getLogger(__name__)


class DatabaseService:
    """
    重构后的数据库服务 - 包含基础设施功能和Schema管理
    职责：数据库连接管理、会话管理、连接池管理、Schema管理
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化数据库服务"""
        if hasattr(self, '_initialized') and self._initialized:
            return

        self.settings = get_settings()

        # 验证数据库类型
        if self.settings.db_type not in ["mysql", "postgresql"]:
            raise ValueError(f"不支持的数据库类型: {self.settings.db_type}。支持MySQL和PostgreSQL")

        # SQLAlchemy引擎配置
        self.sync_engine = None
        self.async_engine = None
        self.session_factory = None
        self.async_session_factory = None
        
        # Schema管理
        self._registered_entities: Dict[str, Type] = {}

        # 初始化SQLAlchemy引擎
        self._init_sqlalchemy_engines()
        
        # 自动注册所有实体
        self._register_all_entities()

        self._initialized = True
        logger.info(f"数据库基础设施服务初始化完成 - 类型: {self.settings.db_type}")

    def _init_sqlalchemy_engines(self):
        """初始化SQLAlchemy引擎"""
        try:
            # 获取数据库URL
            database_url = self.settings.get_database_url()

            # 初始化引擎参数字典
            sync_engine_args: Dict[str, Any] = {
                "echo": self.settings.debug,
            }
            async_engine_args: Dict[str, Any] = {
                "echo": self.settings.debug,
            }

            # 根据数据库类型配置不同的引擎参数
            if "mysql" in database_url:
                # 对于MySQL,异步引擎使用aiomysql,同步引擎使用pymysql
                if "+aiomysql" in database_url:
                    async_database_url = database_url
                    sync_database_url = database_url.replace(
                        "+aiomysql", "+pymysql"
                    )
                elif "+pymysql" in database_url:
                    sync_database_url = database_url
                    async_database_url = database_url.replace(
                        "+pymysql", "+aiomysql"
                    )
                else:
                    # 默认添加驱动
                    sync_database_url = database_url.replace(
                        "mysql://", "mysql+pymysql://"
                    )
                    async_database_url = database_url.replace(
                        "mysql://", "mysql+aiomysql://"
                    )
            elif "postgresql" in database_url:
                # 对于PostgreSQL,异步引擎使用asyncpg,同步引擎使用psycopg2
                if "+psycopg" in database_url:
                    # 已经指定了psycopg(版本3),同步用psycopg2,异步用asyncpg
                    sync_database_url = database_url.replace(
                        "+psycopg", "+psycopg2"
                    )
                    async_database_url = database_url.replace(
                        "+psycopg", "+asyncpg"
                    )
                elif "+asyncpg" in database_url:
                    async_database_url = database_url
                    sync_database_url = database_url.replace(
                        "+asyncpg", "+psycopg2"
                    )
                elif "+psycopg2" in database_url:
                    sync_database_url = database_url
                    async_database_url = database_url.replace(
                        "+psycopg2", "+asyncpg"
                    )
                else:
                    # 默认添加驱动
                    sync_database_url = database_url.replace(
                        "postgresql://", "postgresql+psycopg2://"
                    )
                    async_database_url = database_url.replace(
                        "postgresql://", "postgresql+asyncpg://"
                    )
            else:
                sync_database_url = database_url
                async_database_url = database_url

            # 应用连接池参数
            from sqlalchemy.pool import QueuePool

            # 同步引擎配置 - 可以使用poolclass
            sync_engine_args.update({
                "poolclass": QueuePool,
                "pool_size": self.settings.db_pool_size,
                "max_overflow": self.settings.db_max_overflow,
                "pool_timeout": self.settings.db_pool_timeout,
                "pool_recycle": self.settings.db_pool_recycle,
            })
            # 异步引擎配置 - 不能使用poolclass参数  
            async_engine_args.update({
                "pool_size": self.settings.db_pool_size,
                "max_overflow": self.settings.db_max_overflow,
                "pool_timeout": self.settings.db_pool_timeout,
                "pool_recycle": self.settings.db_pool_recycle,
            })

            # 同步引擎
            self.sync_engine = create_engine(sync_database_url, **sync_engine_args)

            # 异步引擎
            self.async_engine = create_async_engine(async_database_url, **async_engine_args)

            # 会话工厂
            self.session_factory = sessionmaker(
                bind=self.sync_engine, 
                expire_on_commit=False
            )
            self.async_session_factory = async_sessionmaker(
                bind=self.async_engine, 
                class_=AsyncSession, 
                expire_on_commit=False
            )

            logger.info(f"SQLAlchemy引擎初始化成功 - 数据库类型: {self.settings.db_type}")

        except Exception as e:
            logger.error(f"SQLAlchemy引擎初始化失败: {e}")
            raise

    @asynccontextmanager
    async def get_async_session(self):
        """获取异步会话上下文管理器"""
        if self.async_session_factory is None:
            raise RuntimeError("数据库服务未正确初始化")
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    def get_sync_session(self):
        """获取同步会话"""
        if self.session_factory is None:
            raise RuntimeError("数据库服务未正确初始化")
        return self.session_factory()

    async def health_check(self) -> dict[str, Any]:
        """数据库健康检查"""
        try:
            from sqlalchemy import text
            
            # 测试连接
            async with self.get_async_session() as session:
                result = await session.execute(text("SELECT 1 as health_check"))
                health_row = result.fetchone()

            # 根据数据库类型获取版本信息和数据库名
            db_info = None
            db_name = "unknown"
            
            if self.settings.db_type == "mysql":
                # MySQL版本查询
                async with self.get_async_session() as session:
                    result = await session.execute(text("SELECT VERSION() as version"))
                    db_info = result.fetchone()
                    # 获取数据库名
                    result = await session.execute(text("SELECT DATABASE() as db_name"))
                    db_name_row = result.fetchone()
                    db_name = db_name_row[0] if db_name_row else "unknown"
            elif self.settings.db_type == "postgresql":
                # PostgreSQL版本查询
                async with self.get_async_session() as session:
                    result = await session.execute(text("SELECT version() as version"))
                    db_info = result.fetchone()
                    # 获取数据库名
                    result = await session.execute(text("SELECT current_database() as db_name"))
                    db_name_row = result.fetchone()
                    db_name = db_name_row[0] if db_name_row else "unknown"

            return {
                "status": "healthy",
                "database": {
                    "connected": True,
                    "type": self.settings.db_type,
                    "version": db_info[0] if db_info else "unknown",
                    "name": db_name,
                    "host": self.settings.db_host,
                    "port": self.settings.db_port
                }
            }
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "database": {
                    "connected": False,
                    "type": self.settings.db_type,
                    "error": str(e)
                }
            }

    def close(self):
        """关闭数据库连接"""
        try:
            if self.sync_engine:
                self.sync_engine.dispose()
            logger.info("数据库连接已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {e}")

    async def shutdown(self):
        """异步关闭数据库服务"""
        try:
            if self.sync_engine:
                self.sync_engine.dispose()
            if self.async_engine:
                await self.async_engine.dispose()
            logger.info("数据库连接已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {e}")

    def _register_all_entities(self):
        """自动注册所有实体"""
        try:
            # 动态扫描并导入所有实体类
            entities = self._discover_entities()
            
            for entity in entities:
                self.register_entity(entity)
                
            logger.info(f"自动注册了 {len(entities)} 个实体")
            
        except Exception as e:
            logger.error(f"自动注册实体失败: {e}")
    
    def _discover_entities(self) -> List[Type]:
        """动态发现实体类"""
        entities = []
        
        try:
            # 手动注册已知实体（保持向后兼容）
            known_entities = [
                'app.entities.market.Market',
                'app.entities.ticker.Ticker',
                'app.entities.ticker_indicator.TickerIndicator', 
                'app.entities.ticker_score.TickerScore',
                'app.entities.ticker_strategy.TickerStrategy',
                'app.entities.ticker_valuation.TickerValuation'
            ]
            
            for entity_path in known_entities:
                try:
                    module_path, class_name = entity_path.rsplit('.', 1)
                    module = importlib.import_module(module_path)
                    entity_class = getattr(module, class_name)
                    entities.append(entity_class)
                except (ImportError, AttributeError) as e:
                    logger.warning(f"无法导入实体 {entity_path}: {e}")
                    
        except Exception as e:
            logger.error(f"发现实体失败: {e}")
            
        return entities

    def register_entity(self, entity_class: Type) -> None:
        """注册实体类"""
        # 优先使用TABLE_NAME属性
        if hasattr(entity_class, 'TABLE_NAME'):
            table_name = entity_class.TABLE_NAME
        # 兼容SQLAlchemy declarative base
        elif hasattr(entity_class, '__tablename__'):
            table_name = entity_class.__tablename__
        else:
            logger.warning(f"实体 {entity_class.__name__} 缺少TABLE_NAME或__tablename__属性")
            return
            
        self._registered_entities[table_name] = entity_class
        logger.info(f"注册实体: {entity_class.__name__} -> {table_name}")

    def get_registered_entities(self) -> Dict[str, Type]:
        """获取已注册的实体"""
        return self._registered_entities.copy()

    async def check_table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        try:
            async with self.get_async_session() as session:
                if self.settings.db_type == "mysql":
                    result = await session.execute(text("""
                        SELECT COUNT(*) as count 
                        FROM information_schema.tables 
                        WHERE table_schema = DATABASE() 
                        AND table_name = :table_name
                    """), {"table_name": table_name})
                elif self.settings.db_type == "postgresql":
                    result = await session.execute(text("""
                        SELECT COUNT(*) as count 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = :table_name
                    """), {"table_name": table_name})
                else:
                    return False
                
                count = result.scalar()
                return (count or 0) > 0
        except Exception as e:
            logger.error(f"检查表存在性失败: {table_name}, 错误: {e}")
            return False

    async def sync_schema(self) -> Dict[str, Any]:
        """同步数据库模式"""
        sync_results = {
            "created": [],
            "existing": [],
            "failed": [],
            "summary": {}
        }
        
        # 如果有注册的实体，使用自定义逻辑
        if self._registered_entities:
            for table_name, entity_class in self._registered_entities.items():
                try:
                    exists = await self.check_table_exists(table_name)
                    
                    if not exists:
                        # 表不存在，尝试创建表
                        if hasattr(entity_class, 'TABLE_SCHEMA'):
                            async with self.get_async_session() as session:
                                await session.execute(text(entity_class.TABLE_SCHEMA))
                                await session.commit()
                            sync_results["created"].append(table_name)
                            logger.info(f"✅ 创建表: {table_name}")
                        else:
                            sync_results["failed"].append({
                                "table": table_name,
                                "error": "缺少TABLE_SCHEMA属性"
                            })
                    else:
                        sync_results["existing"].append(table_name)
                        logger.info(f"📋 表已存在: {table_name}")
                        
                except Exception as e:
                    sync_results["failed"].append({
                        "table": table_name,
                        "error": str(e)
                    })
                    logger.error(f"❌ 同步表失败: {table_name}, 错误: {e}")
        else:
            # 使用SQLAlchemy metadata创建表
            try:
                if self.async_engine is not None:
                    async with self.async_engine.begin() as conn:
                        await conn.run_sync(Base.metadata.create_all)
                    sync_results["created"].append("all_tables")
                    logger.info("✅ 使用SQLAlchemy metadata创建所有表")
                else:
                    raise RuntimeError("异步引擎未初始化")
            except Exception as e:
                sync_results["failed"].append({
                    "table": "all_tables",
                    "error": str(e)
                })
                logger.error(f"❌ 创建表失败: {e}")
        
        sync_results["summary"] = {
            "total": len(self._registered_entities) or 1,
            "created": len(sync_results["created"]),
            "existing": len(sync_results["existing"]),
            "failed": len(sync_results["failed"])
        }
        
        return sync_results

    async def validate_schema(self) -> Dict[str, Any]:
        """验证数据库模式"""
        validation_results = {
            "valid": [],
            "missing": [],
            "errors": [],
            "summary": {}
        }
        
        for table_name, entity_class in self._registered_entities.items():
            try:
                exists = await self.check_table_exists(table_name)
                
                if exists:
                    validation_results["valid"].append(table_name)
                else:
                    validation_results["missing"].append(table_name)
                    
            except Exception as e:
                validation_results["errors"].append({
                    "table": table_name,
                    "error": str(e)
                })
        
        validation_results["summary"] = {
            "total": len(self._registered_entities),
            "valid": len(validation_results["valid"]),
            "missing": len(validation_results["missing"]),
            "errors": len(validation_results["errors"])
        }
        
        return validation_results

    async def create_tables(self):
        """创建所有必要的数据库表 - 使用内置Schema管理"""
        try:
            result = await self.sync_schema()
            
            if result["summary"]["failed"] > 0:
                logger.warning(f"部分表创建失败: {result['failed']}")
            
            logger.info(f"数据库表同步完成: 创建 {result['summary']['created']} 个表，已存在 {result['summary']['existing']} 个表")
            
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}")
            raise


# 保留的全局实例和依赖注入
_database_service: Optional[DatabaseService] = None
_db_lock = threading.Lock()


def get_database_service() -> DatabaseService:
    """获取数据库服务单例实例"""
    global _database_service

    if _database_service is None:
        with _db_lock:
            if _database_service is None:
                _database_service = DatabaseService()

    return _database_service


# 保留的依赖注入函数
async def get_async_db_session():
    """获取异步数据库会话(FastAPI依赖注入)"""
    db_service = get_database_service()
    async with db_service.get_async_session() as session:
        yield session


def get_sync_db_session():
    """获取同步数据库会话(FastAPI依赖注入)"""
    db_service = get_database_service()
    return db_service.get_sync_session()


# Schema管理的便捷函数
async def sync_database_schema() -> Dict[str, Any]:
    """同步数据库模式的便捷函数"""
    db_service = get_database_service()
    return await db_service.sync_schema()


async def validate_database_schema() -> Dict[str, Any]:
    """验证数据库模式的便捷函数"""
    db_service = get_database_service()
    return await db_service.validate_schema()


def get_schema_manager():
    """获取Schema管理器实例（向后兼容）"""
    return get_database_service()
