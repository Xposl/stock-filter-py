"""
Ticker TrendFastAPI 主应用
集成 PocketFlow、简化的gRPC认证服务
"""

import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

# 导入简化的认证模块
from app.auth.grpc_auth_client import cleanup_auth_client
from app.auth.auth_middleware import AuthMiddleware

# 导入配置和服务
from app.config import get_settings

# 导入日志配置
from app.logging_config import get_logger, setup_logging

from app.services.auth_service import get_auth_service, cleanup_auth_service
from app.services.database_service import get_database_service

# 获取日志器
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    settings = get_settings()

    # 配置日志系统
    log_config = setup_logging(log_level=settings.log_level)
    logger.info(f"✅ 日志系统已配置: {log_config['log_file']}")

    logger.info(f"启动 {settings.app_name} v{settings.app_version}")

    try:
        # 1. 初始化认证服务
        logger.info("🔧 初始化认证服务...")
        auth_service = get_auth_service()
        if auth_service.is_test_mode():
            logger.info("⚠️  认证服务运行在测试模式")
        else:
            # 测试gRPC连接
            health_status = await auth_service.health_check()
            if health_status["grpc_connected"]:
                logger.info("✅ gRPC认证服务连接成功")
            else:
                logger.warning("⚠️ gRPC认证服务连接失败，但继续运行...")

        # 2. 初始化数据库服务
        logger.info("🔧 初始化数据库服务...")
        database_service = get_database_service()

        # 创建数据表
        try:
            await database_service.create_tables()
            logger.info("✅ 数据库表结构创建成功")
        except Exception as e:
            logger.warning(f"⚠️ 数据库表创建失败: {e}")

        # 3. 初始化Agent服务
        logger.info("🔧 初始化Agent服务...")
        try:
            from app.agents.service import get_agent_service
            agent_service = await get_agent_service()
            agent_stats = agent_service.get_agent_statistics()
            logger.info(f"✅ Agent服务初始化完成 - 已加载 {agent_stats['loaded_agents']}/{agent_stats['total_agents']} 个Agent")
        except Exception as e:
            logger.warning(f"⚠️ Agent服务初始化失败: {e}")

        logger.info(f"�� {settings.app_name} 启动成功!")
        logger.info(f"📡 服务地址: http://{settings.host}:{settings.port}")
        logger.info(f"📚 API文档: http://{settings.host}:{settings.port}/docs")

    except Exception as e:
        logger.error(f"❌ 启动失败: {e!s}")
        raise

    # 应用运行期间
    yield {"settings": settings}

    # 应用关闭时的清理工作
    logger.info("🔄 正在关闭应用...")

    try:
        # 1. 清理认证服务
        logger.info("关闭认证服务...")
        await cleanup_auth_service()
        
        # 2. 清理gRPC认证客户端
        logger.info("关闭gRPC认证客户端...")
        await cleanup_auth_client()

        # 3. 关闭数据库服务
        logger.info("关闭数据库服务...")
        await database_service.shutdown()

        logger.info("✅ 应用关闭完成")

    except Exception as e:
        logger.error(f"❌ 关闭时发生错误: {e!s}")


# 创建FastAPI应用
def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="股票趋势分析工具",
        version=settings.app_version,
        lifespan=lifespan,
        debug=settings.debug,
    )

    # 配置中间件
    setup_middleware(app, settings)
    
    # 配置路由
    setup_routes(app)
    
    # 配置异常处理
    setup_exception_handlers(app)

    return app


def setup_middleware(app: FastAPI, settings):
    """配置中间件"""
    
    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_credentials,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
    )

    # 受信任主机中间件
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.trusted_hosts,
    )

    # 可选认证中间件（支持匿名访问）
    # 使用配置中的排除路径
    app.add_middleware(AuthMiddleware)

    # 请求日志中间件
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """记录HTTP请求"""
        start_time = asyncio.get_event_loop().time()
        
        # 处理请求
        response = await call_next(request)
        
        # 计算处理时间
        process_time = asyncio.get_event_loop().time() - start_time
        
        # 记录日志（排除健康检查）
        if not request.url.path.startswith("/health"):
            user_info = getattr(request.state, 'user', None)
            user_id = user_info['user_id'] if user_info else "anonymous"
            
            logger.info(
                f"{request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.3f}s - "
                f"User: {user_id}"
            )
        
        # 添加处理时间到响应头
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


def setup_routes(app: FastAPI):
    """配置路由"""
    
    # 包含所有API路由
    from app.routers import ticker_router, scheduler_router
    app.include_router(ticker_router)
    app.include_router(scheduler_router)

    # 健康检查端点
    @app.get("/health", tags=["健康检查"])
    async def health_check():
        """应用健康检查"""
        try:
            # 检查认证服务
            auth_service = get_auth_service()
            auth_health = await auth_service.health_check()
            
            # 检查数据库服务
            database_service = get_database_service()
            db_health = await database_service.health_check()
            
            overall_status = "healthy"
            if auth_health["status"] != "healthy" or not db_health:
                overall_status = "degraded"
            
            return {
                "status": overall_status,
                "timestamp": asyncio.get_event_loop().time(),
                "services": {
                    "auth": auth_health,
                    "database": {"status": "healthy" if db_health else "unhealthy"}
                }
            }
        except Exception as e:
            logger.error(f"健康检查失败: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": asyncio.get_event_loop().time()
            }

    # 服务信息端点
    @app.get("/info", tags=["服务信息"])
    async def service_info():
        """获取服务信息"""
        settings = get_settings()
        auth_service = get_auth_service()
        
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "description": "股票趋势分析工具",
            "auth_mode": "test" if auth_service.is_test_mode() else "production",
            "features": {
                "grpc_auth": True,
                "test_mode": auth_service.is_test_mode(),
                "agents": True,
                "memory": True
            }
        }

    # 根路径
    @app.get("/", tags=["首页"])
    async def root():
        """根路径重定向到文档"""
        return {"message": "Ticker TrendFastAPI 服务", "docs": "/docs"}


def setup_exception_handlers(app: FastAPI):
    """配置异常处理器"""
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """HTTP异常处理"""
        logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail} - Path: {request.url.path}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.status_code,
                "message": exc.detail,
                "path": str(request.url.path)
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """通用异常处理"""
        logger.error(f"未处理的异常: {exc} - Path: {request.url.path}", exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": 500,
                "message": "内部服务器错误",
                "path": str(request.url.path)
            }
        )


# 应用实例
app = create_app()

# 主程序入口
if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
