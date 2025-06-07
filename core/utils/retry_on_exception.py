"""
Handler模块通用工具函数
Args:
    max_retries: 最大重试次数
    delay: 初始延迟时间（秒）
    backoff: 延迟时间的倍数增长
    exceptions: 需要捕获的异常类型
Returns:
    函数执行结果或者在达到最大重试次数后抛出异常
"""
import logging
import random
import time
from functools import wraps

# 配置日志
logger = logging.getLogger(__name__)


def retry_on_exception(max_retries=3, delay=5, backoff=2, exceptions=(Exception,)):
    """重试函数执行的装饰器

    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟时间的倍数增长
        exceptions: 需要捕获的异常类型

    Returns:
        函数执行结果或者在达到最大重试次数后抛出异常
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            mtries, mdelay = max_retries, delay
            while mtries > 0:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    mtries -= 1
                    if mtries == 0:
                        logger.error(f"函数 {func.__name__} 达到最大重试次数 {max_retries}")
                        raise

                    # 添加随机抖动，避免同时重试
                    jitter = random.uniform(0.1, 0.5)
                    sleep_time = mdelay + jitter

                    logger.warning(f"函数 {func.__name__} 调用失败，错误: {str(e)}")
                    logger.warning(f"将在 {sleep_time:.2f} 秒后重试，剩余重试次数: {mtries}")

                    time.sleep(sleep_time)
                    mdelay *= backoff

        return wrapper

    return decorator
