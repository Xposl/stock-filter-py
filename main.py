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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

def setup_auth():
    """设置鉴权服务"""
    # 加载环境变量中的鉴权设置
    auth_enabled = os.getenv("AUTH_ENABLED", "true").lower() == "true"
    
    if auth_enabled:
        logger.info("鉴权服务已启用")
        # 预加载auth_client以测试连接
        try:
            from core.auth.auth_grpc_client import auth_client
            logger.info("鉴权服务客户端初始化完成")
        except ImportError:
            logger.warning("鉴权服务客户端导入失败，请确保已生成gRPC代码")
        except Exception as e:
            logger.warning(f"鉴权服务客户端初始化异常: {str(e)}")
    else:
        logger.info("鉴权服务已禁用")

def start_server(config: Optional[ServerConfig] = None):
    if config is None:
        config = ServerConfig()
    
    # 设置gRPC和鉴权服务
    try:
        setup_grpc()
        setup_auth()
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
