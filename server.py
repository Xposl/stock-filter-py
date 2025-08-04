#!/usr/bin/env python3
"""
Ticker Trend 服务启动脚本
支持开发模式、生产模式和Docker模式
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 切换到项目根目录（api目录）
os.chdir(project_root)


def setup_logging(level: str = "INFO"):
    """设置日志配置"""
    # 确保logs目录存在
    import os
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("logs/ticker-trend.log", encoding="utf-8"),
        ],
    )


def check_environment():
    """检查环境配置"""
    logger = logging.getLogger(__name__)

    # 使用配置管理而不是直接检查环境变量
    try:
        # 添加相对路径到系统路径
        sys.path.insert(0, str(project_root))
        from app.config import get_settings
        
        config = get_settings()
        
        # 检查关键配置是否存在
        missing_configs = []
        if not config.platform_id:
            missing_configs.append("platform_id")
        if not config.client_secret:
            missing_configs.append("client_secret")
        if missing_configs:
            logger.warning(f"缺少关键配置: {', '.join(missing_configs)}")
            logger.info("请检查 .env 文件或设置相应的环境变量")
            
    except ImportError as e:
        logger.error(f"无法导入配置模块: {e}")
        logger.info("将跳过配置检查")
    except Exception as e:
        logger.error(f"配置检查失败: {e}")
        logger.info("将跳过配置检查")

    # 检查关键目录
    dirs_to_check = ["logs", "config", "temp"]
    for dir_name in dirs_to_check:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"创建目录: {dir_path}")


def start_development():
    """启动开发模式"""
    logger = logging.getLogger(__name__)
    logger.info("🔧 启动开发模式...")

    # 设置开发环境变量
    os.environ["DEBUG"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"

    import uvicorn
    from app.config import get_settings
    
    settings = get_settings()

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,  # 使用配置的端口
        reload=True,
        log_level="debug",
        access_log=True,
        reload_dirs=[str(project_root / "app"), str(project_root / "ai_agent")],
    )


def start_production():
    """启动生产模式"""
    logger = logging.getLogger(__name__)
    logger.info("🚀 启动生产模式...")

    # 设置生产环境变量
    os.environ["DEBUG"] = "false"
    os.environ.setdefault("LOG_LEVEL", "INFO")

    import uvicorn

    from app.config import get_settings

    settings = get_settings()

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        workers=settings.max_workers,
        log_level=settings.log_level.lower(),
        access_log=False,  # 生产环境使用自定义日志
        loop="uvloop",  # 使用更高性能的事件循环
        http="httptools",  # 使用更高性能的HTTP解析器
    )


def start_docker():
    """Docker容器模式启动"""
    logger = logging.getLogger(__name__)
    logger.info("🐳 启动Docker模式...")

    # Docker环境通常不需要重载
    os.environ["DEBUG"] = "false"

    import uvicorn

    from app.config import get_settings

    settings = get_settings()

    # Docker模式使用单worker以避免资源争用
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",  # Docker内部需要绑定所有接口
        port=settings.port,
        workers=1,
        log_level=settings.log_level.lower(),
        access_log=True,
    )


def install_dependencies():
    """安装依赖"""
    logger = logging.getLogger(__name__)
    logger.info("📦 安装Python依赖...")

    import subprocess

    try:
        # 安装requirements.txt中的依赖
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
            cwd=project_root,
        )

        logger.info("✅ 依赖安装完成")

    except subprocess.CalledProcessError as e:
        logger.error(f"❌ 依赖安装失败: {e}")
        sys.exit(1)


def check_dependencies():
    """检查依赖是否安装"""
    logger = logging.getLogger(__name__)

    required_packages = ["fastapi", "uvicorn", "pydantic", "httpx"]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        logger.warning(f"缺少依赖包: {', '.join(missing_packages)}")
        logger.info("运行 'python server.py --install' 安装依赖")
        return False

    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Ticker Trend服务启动脚本")
    parser.add_argument(
        "--mode",
        choices=["dev", "prod", "docker"],
        default="dev",
        help="启动模式 (默认: dev)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="日志级别 (默认: INFO)",
    )
    parser.add_argument("--install", action="store_true", help="安装依赖并退出")
    parser.add_argument("--check", action="store_true", help="检查环境并退出")

    args = parser.parse_args()

    # 设置日志
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    logger.info("🌟 Ticker Trend服务启动脚本")
    logger.info(f"📁 项目根目录: {project_root}")

    # 检查环境
    check_environment()

    # 安装依赖
    if args.install:
        install_dependencies()
        return

    # 环境检查
    if args.check:
        logger.info("🔍 检查环境配置...")

        if check_dependencies():
            logger.info("✅ 所有依赖已安装")
        else:
            logger.error("❌ 存在缺失的依赖")
            sys.exit(1)

        logger.info("✅ 环境检查完成")
        return

    # 依赖检查
    if not check_dependencies():
        logger.error("❌ 请先安装依赖: python server.py --install")
        sys.exit(1)

    # 根据模式启动服务
    try:
        if args.mode == "dev":
            start_development()
        elif args.mode == "prod":
            start_production()
        elif args.mode == "docker":
            start_docker()

    except KeyboardInterrupt:
        logger.info("👋 用户中断,正在关闭服务...")
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 