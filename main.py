import uvicorn
from api.api import app
import argparse
import logging
from typing import Optional
from dotenv import load_dotenv
import os
import subprocess
import sys

# 加载.env文件
load_dotenv()

# 抑制gRPC相关的警告日志
os.environ.setdefault('GRPC_VERBOSITY', 'ERROR')
os.environ.setdefault('GRPC_TRACE', '')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 抑制absl日志警告
try:
    import grpc
    import logging as absl_logging
    # 设置gRPC日志级别为ERROR，避免INFO级别的警告
    grpc_logger = logging.getLogger('grpc')
    grpc_logger.setLevel(logging.ERROR)
    
    # 初始化absl日志系统（如果可用）
    try:
        from absl import logging as absl_logging
        absl_logging.set_verbosity(absl_logging.ERROR)
    except ImportError:
        pass
except ImportError:
    pass

class ServerConfig:
    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        reload: bool = False,
        workers: int = 1
    ):
        self.host = host
        self.port = port
        self.reload = reload
        self.workers = workers

def setup_grpc():
    """设置gRPC服务，生成Python代码"""
    try:
        # 检查是否已经生成了gRPC代码
        grpc_dir = os.path.join(os.path.dirname(__file__), "core/grpc/auth")
        if not os.path.exists(grpc_dir):
            logger.info("正在生成gRPC代码...")
            gen_script = os.path.join(os.path.dirname(__file__), "tools/generate_grpc_code.py")
            subprocess.run([sys.executable, gen_script], check=True)
            logger.info("gRPC代码生成完成")
        else:
            logger.info("gRPC代码目录已存在，跳过生成")
    except Exception as e:
        logger.error(f"生成gRPC代码失败: {str(e)}")
        raise

def setup_auth(test_connection: bool = True):
    """设置鉴权服务"""
    # 加载环境变量中的鉴权设置
    auth_enabled = os.getenv("AUTH_ENABLED", "true").lower() == "true"
    
    if auth_enabled:
        logger.info("鉴权服务已启用")
        # 记录认证服务配置信息
        auth_host = os.getenv("AUTH_SERVICE_HOST", "localhost")
        auth_port = os.getenv("AUTH_SERVICE_PORT", "9091")
        logger.info(f"认证服务配置: {auth_host}:{auth_port}")
        
        # 在reload模式下跳过连接测试，避免fork警告
        if test_connection:
            # 预加载auth_client以测试连接
            try:
                from core.auth.auth_grpc_client import auth_client
                
                # 测试gRPC连接
                try:
                    import grpc
                    channel = grpc.insecure_channel(f"{auth_host}:{auth_port}")
                    # 设置较短的超时时间来测试连接
                    ready = grpc.channel_ready_future(channel).result(timeout=5)
                    logger.info("鉴权服务连接测试成功")
                    channel.close()  # 立即关闭测试连接
                except grpc.FutureTimeoutError:
                    logger.error("鉴权服务连接超时，请确认服务地址和端口正确，且服务已启动")
                except Exception as conn_err:
                    logger.error(f"鉴权服务连接测试失败: {str(conn_err)}")
                
                logger.info("鉴权服务客户端初始化完成")
            except ImportError:
                logger.warning("鉴权服务客户端导入失败，请确保已生成gRPC代码")
                logger.info("尝试自动生成gRPC代码...")
                try:
                    setup_grpc()
                    logger.info("gRPC代码生成完成，请重启服务")
                except Exception as gen_err:
                    logger.error(f"gRPC代码生成失败: {str(gen_err)}")
            except Exception as e:
                logger.warning(f"鉴权服务客户端初始化异常: {str(e)}")
        else:
            logger.info("跳过鉴权服务连接测试（reload模式）")
    else:
        logger.info("鉴权服务已禁用")

def start_server(config: Optional[ServerConfig] = None):
    if config is None:
        config = ServerConfig()
    
    # 设置gRPC和鉴权服务
    try:
        setup_grpc()
        # 在reload模式下跳过连接测试以避免fork警告
        setup_auth(test_connection=not config.reload)
    except Exception as e:
        logger.error(f"服务初始化失败: {str(e)}")
        # 继续启动，但可能鉴权功能不可用
    
    logger.info(f"Starting server on {config.host}:{config.port}")
    uvicorn.run(
        "api.api:app",
        host=config.host,
        port=config.port,
        reload=config.reload,
        workers=config.workers
    )

def parse_args():
    parser = argparse.ArgumentParser(description="InvestNote API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Bind socket to this host")
    parser.add_argument("--port", type=int, default=8000, help="Bind socket to this port")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    config = ServerConfig(
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers
    )
    start_server(config)
