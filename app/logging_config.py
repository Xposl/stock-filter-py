import logging
import logging.handlers
import os
from datetime import datetime
from typing import Any, Dict, Optional

from app.config import Settings, get_settings


def setup_logging(
    log_level: str = "INFO", log_format: Optional[str] = None
) -> Dict[str, Any]:
    """
    配置应用日志系统
    支持控制台输出和文件输出到logs目录
    """

    # 确保logs目录存在
    os.makedirs("logs", exist_ok=True)

    # 生成日志文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/agent-{timestamp}.log"

    # 从配置获取日志格式，如果未提供则使用默认值
    settings: Settings = get_settings()
    log_format = log_format or settings.log_format
    date_format = "%Y-%m-%d %H:%M:%S"

    # 清除现有的handlers,避免重复日志
    logging.getLogger().handlers.clear()

    # 设置根logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # 创建formatter
    formatter = logging.Formatter(log_format, date_format)

    # 控制台输出handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_handler.setFormatter(formatter)

    # 文件输出handler (支持日志轮转)
    file_handler = logging.handlers.RotatingFileHandler(
        log_filename, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"  # 10MB
    )
    file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    file_handler.setFormatter(formatter)

    # 添加handlers到根logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # 设置特定库的日志级别,避免过于详细的日志
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # 返回配置信息
    return {
        "log_level": log_level,
        "log_file": log_filename,
        "handlers": ["console", "file"],
        "status": "configured",
    }


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """获取配置好的logger实例"""
    return logging.getLogger(name)


# 创建默认的logger实例，供其他模块直接导入使用
logger = get_logger(__name__)
