import uvicorn
from api.api import app
import argparse
import logging
from typing import Optional
from dotenv import load_dotenv
import os

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

def start_server(config: Optional[ServerConfig] = None):
    if config is None:
        config = ServerConfig()
    
    logger.info(f"Starting server on {config.host}:{config.port}")
    uvicorn.run(
        "api:app",
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
