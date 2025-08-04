from functools import lru_cache
from typing import Optional
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    应用程序配置设置 - 支持单例模式和gRPC认证服务集成
    所有配置优先从环境变量获取
    """
    
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # 应用程序设置
    app_name: str = "InvestNote"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 测试模式配置 🆕
    test_mode: bool = False  # 是否启用测试模式（绕过第三方认证）
    test_user_id: str = "0"  # 测试模式下的默认用户ID
    test_username: str = "test_user"  # 测试模式下的默认用户名

    # 服务器设置
    host: str = "0.0.0.0"
    port: int = 8000

    # 运行模式配置
    singleton_mode: bool = True  # 默认启用单例模式

    # 千问模型配置 (核心配置)
    dashscope_api_key: Optional[str] = None  # 千问API密钥

    # 认证服务配置 (gRPC) - 统一配置
    auth_enabled: bool = True
    # 单例模式配置 (当nacos_enabled=False时使用)
    auth_service_host: str = "localhost"
    auth_service_port: int = 9091
    # Nacos服务发现配置 (当nacos_enabled=True时使用) 🆕
    auth_service_name: str = "auth-service"
    # 认证服务通用配置
    auth_timeout: int = 30
    auth_retry_max: int = 3
    auth_retry_delay: float = 1.0
    
    # 认证排除路径配置 🆕
    auth_exclude_paths: list[str] = [
        "/health",
        "/info", 
        "/docs",
        "/redoc",
        "/openapi.json",
        "/static",
        "/favicon.ico"
    ]

    # Nacos 配置 (可选关闭)
    nacos_enabled: bool = False  # 默认关闭Nacos
    nacos_server_url: str = "http://localhost:8848"
    nacos_namespace: str = "ai-service"
    nacos_group: str = "DEFAULT_GROUP"
    nacos_username: str = "nacos"
    nacos_password: str = "nacos"
    nacos_data_id: str = "ai-service-config.yaml"

    # 服务注册配置 (仅在nacos_enabled时使用)
    service_name: str = "ai-chatbot-service"
    service_ip: str = "127.0.0.1"
    service_port: int = 8000
    service_weight: float = 1.0
    service_enabled: bool = True
    service_healthy: bool = True
    service_metadata: dict = {}

    # 平台配置
    platform_id: str = ""
    client_secret: str = ""

    # 数据库配置
    db_type: str = "mysql"  # 默认使用MySQL (生产环境友好)
    database_url: Optional[str] = None
    
    # MySQL配置 (默认)
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "ai_chatbot"
    db_user: str = "root"
    db_password: str = ""

    # PostgreSQL配置 (可选)
    # 使用时设置db_type="postgresql"并配置相应参数

    # 数据库连接配置
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600

    # Redis 配置
    redis_url: Optional[str] = None
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0

    # PocketFlow 设置
    pocketflow_config_path: Optional[str] = "./config/pocketflow.yaml"
    pocketflow_log_level: str = "INFO"

    # 日志设置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 性能配置
    max_workers: int = 4
    request_timeout: int = 30
    connection_pool_size: int = 10

    # CORS 配置
    cors_origins: list[str] = ["*"]
    cors_credentials: bool = True
    cors_methods: list[str] = ["*"]
    cors_headers: list[str] = ["*"]
    
    # 受信任主机配置 🆕
    trusted_hosts: list[str] = ["*"]

    # 环境标识
    environment: str = "development"  # development, staging, production


    def get_redis_url(self) -> str:
        """构建Redis连接字符串"""
        if self.redis_url:
            return self.redis_url

        auth_part = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth_part}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    def get_database_url(self) -> str:
        """
        根据配置构建数据库连接URL。
        支持MySQL和PostgreSQL。
        """
        if self.database_url:
            return self.database_url

        database_type = self.db_type.lower()
        user_encoded = quote_plus(self.db_user)
        password_encoded = quote_plus(self.db_password)

        if database_type == "mysql":
            return f"mysql+aiomysql://{user_encoded}:{password_encoded}@{self.db_host}:{self.db_port}/{self.db_name}"
        elif database_type == "postgresql":
            return f"postgresql+psycopg://{user_encoded}:{password_encoded}@{self.db_host}:{self.db_port}/{self.db_name}"
        else:
            raise ValueError(f"不支持的数据库类型: {database_type}")

    def get_auth_connection_mode(self) -> str:
        """获取认证连接模式"""
        return "nacos" if self.nacos_enabled else "singleton"


# 全局配置实例 (单例模式)
_settings_instance: Optional[Settings] = None


@lru_cache
def get_settings() -> Settings:
    """获取配置实例 (使用lru_cache实现单例模式)"""
    return Settings()


# =================== 辅助函数 ===================


def is_test_mode() -> bool:
    """判断是否为测试模式"""
    return get_settings().test_mode


def get_test_user_info() -> dict:
    """获取测试模式下的用户信息"""
    config = get_settings()
    return {
        "user_id": config.test_user_id,
        "username": config.test_username,
        "email": f"{config.test_username}@test.local",
        "nickname": "测试用户",
        "avatar": "",
        "platform_id": config.platform_id or "test_platform",
        "client_id": "test_client",
        "roles": ["user", "admin"],  # 默认授予测试用户admin权限
        "authorities": ["*"],  # 默认授予所有权限
        "metadata": {"mode": "test"},
    }



