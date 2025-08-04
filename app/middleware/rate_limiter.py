"""
Rate Limiting Middleware - 任务 22.3 实现
防止API滥用，确保公平使用，支持基于用户、IP和端点的限制策略
"""

import time
import asyncio
import logging
import functools
import inspect
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque
from datetime import datetime, timedelta
from enum import Enum

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimitStrategy(str, Enum):
    """限流策略类型"""
    FIXED_WINDOW = "fixed_window"     # 固定窗口
    SLIDING_WINDOW = "sliding_window" # 滑动窗口
    TOKEN_BUCKET = "token_bucket"     # 令牌桶


@dataclass
class RateLimitRule:
    """限流规则配置"""
    requests_per_window: int  # 窗口内允许的请求数
    window_size: int         # 窗口大小（秒）
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    burst_limit: Optional[int] = None  # 突发限制（令牌桶策略）


@dataclass 
class RateLimitResult:
    """限流检查结果"""
    allowed: bool
    remaining: int
    reset_time: float
    retry_after: Optional[int] = None


class SlidingWindowCounter:
    """滑动窗口计数器"""
    
    def __init__(self, window_size: int, max_requests: int):
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests = deque()  # 存储请求时间戳
        
    def is_allowed(self) -> Tuple[bool, int, float]:
        """检查是否允许请求"""
        now = time.time()
        window_start = now - self.window_size
        
        # 清理过期请求
        while self.requests and self.requests[0] <= window_start:
            self.requests.popleft()
        
        # 检查是否超限
        if len(self.requests) >= self.max_requests:
            # 计算重置时间（最早请求过期时间）
            reset_time = self.requests[0] + self.window_size
            return False, 0, reset_time
        
        # 允许请求，记录时间戳
        self.requests.append(now)
        remaining = self.max_requests - len(self.requests)
        reset_time = now + self.window_size
        
        return True, remaining, reset_time


class TokenBucket:
    """令牌桶限流器"""
    
    def __init__(self, capacity: int, refill_rate: float, burst_limit: Optional[int] = None):
        self.capacity = capacity
        self.refill_rate = refill_rate  # 每秒添加的令牌数
        self.burst_limit = burst_limit or capacity
        self.tokens = float(capacity)
        self.last_refill = time.time()
        
    def is_allowed(self, tokens_requested: int = 1) -> Tuple[bool, int, float]:
        """检查是否有足够令牌"""
        now = time.time()
        
        # 计算需要添加的令牌数
        time_passed = now - self.last_refill
        tokens_to_add = time_passed * self.refill_rate
        
        # 更新令牌数（不超过容量）
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
        
        # 检查是否有足够令牌
        if self.tokens >= tokens_requested:
            self.tokens -= tokens_requested
            remaining = int(self.tokens)
            reset_time = now + (self.capacity - self.tokens) / self.refill_rate
            return True, remaining, reset_time
        else:
            # 计算需要等待的时间
            tokens_needed = tokens_requested - self.tokens
            wait_time = tokens_needed / self.refill_rate
            reset_time = now + wait_time
            return False, 0, reset_time


class RateLimiter:
    """统一限流管理器"""
    
    def __init__(self):
        self.user_limiters: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.ip_limiters: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.global_limiters: Dict[str, Any] = {}
        
        # 默认限流规则
        self.default_rules = {
            "chat_message": RateLimitRule(
                requests_per_window=60,  # 60次/分钟
                window_size=60,
                strategy=RateLimitStrategy.SLIDING_WINDOW
            ),
            "chat_stream": RateLimitRule(
                requests_per_window=30,  # 30次/分钟（流式更消耗资源）
                window_size=60,
                strategy=RateLimitStrategy.SLIDING_WINDOW
            ),
            "conversation_create": RateLimitRule(
                requests_per_window=10,  # 10次/分钟
                window_size=60,
                strategy=RateLimitStrategy.SLIDING_WINDOW
            ),
            "agent_management": RateLimitRule(
                requests_per_window=20,  # 20次/分钟
                window_size=60,
                strategy=RateLimitStrategy.SLIDING_WINDOW
            ),
            "search": RateLimitRule(
                requests_per_window=100, # 100次/分钟
                window_size=60,
                strategy=RateLimitStrategy.SLIDING_WINDOW
            ),
            "global": RateLimitRule(
                requests_per_window=1000,  # 全局1000次/分钟
                window_size=60,
                strategy=RateLimitStrategy.TOKEN_BUCKET,
                burst_limit=1200
            )
        }
        
    def _get_limiter_key(self, endpoint: str, user_id: Optional[str] = None, 
                        ip_address: Optional[str] = None) -> str:
        """生成限流器键名"""
        if user_id:
            return f"user:{user_id}:{endpoint}"
        elif ip_address:
            return f"ip:{ip_address}:{endpoint}"
        else:
            return f"global:{endpoint}"
    
    def _get_or_create_limiter(self, key: str, rule: RateLimitRule) -> Any:
        """获取或创建限流器实例"""
        storage = self.global_limiters
        
        if key.startswith("user:"):
            user_id = key.split(":")[1]
            storage = self.user_limiters[user_id]
        elif key.startswith("ip:"):
            ip = key.split(":")[1]
            storage = self.ip_limiters[ip]
        
        if key not in storage:
            if rule.strategy == RateLimitStrategy.TOKEN_BUCKET:
                refill_rate = rule.requests_per_window / rule.window_size
                storage[key] = TokenBucket(
                    capacity=rule.requests_per_window,
                    refill_rate=refill_rate,
                    burst_limit=rule.burst_limit
                )
            else:  # SLIDING_WINDOW
                storage[key] = SlidingWindowCounter(
                    window_size=rule.window_size,
                    max_requests=rule.requests_per_window
                )
        
        return storage[key]
    
    def check_rate_limit(self, endpoint: str, user_id: Optional[str] = None,
                        ip_address: Optional[str] = None, 
                        custom_rule: Optional[RateLimitRule] = None) -> RateLimitResult:
        """检查是否触发限流"""
        
        # 使用自定义规则或默认规则
        rule = custom_rule or self.default_rules.get(endpoint, self.default_rules["global"])
        
        # 检查用户级限流
        if user_id:
            user_key = self._get_limiter_key(endpoint, user_id=user_id)
            user_limiter = self._get_or_create_limiter(user_key, rule)
            allowed, remaining, reset_time = user_limiter.is_allowed()
            
            if not allowed:
                retry_after = max(1, int(reset_time - time.time()))
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=reset_time,
                    retry_after=retry_after
                )
        
        # 检查IP级限流
        if ip_address:
            ip_key = self._get_limiter_key(endpoint, ip_address=ip_address)
            ip_limiter = self._get_or_create_limiter(ip_key, rule)
            allowed, remaining, reset_time = ip_limiter.is_allowed()
            
            if not allowed:
                retry_after = max(1, int(reset_time - time.time()))
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_time=reset_time,
                    retry_after=retry_after
                )
        
        # 检查全局限流
        global_key = self._get_limiter_key("global")
        global_rule = self.default_rules["global"]
        global_limiter = self._get_or_create_limiter(global_key, global_rule)
        allowed, remaining, reset_time = global_limiter.is_allowed()
        
        if not allowed:
            retry_after = max(1, int(reset_time - time.time()))
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_time=reset_time,
                retry_after=retry_after
            )
        
        # 全部检查通过
        return RateLimitResult(
            allowed=True,
            remaining=remaining,
            reset_time=reset_time
        )
    
    def cleanup_expired_limiters(self):
        """清理过期的限流器实例（定期调用）"""
        now = time.time()
        
        # 清理用户限流器（保留最近1小时活跃的）
        for user_id in list(self.user_limiters.keys()):
            user_limiters = self.user_limiters[user_id]
            for key in list(user_limiters.keys()):
                limiter = user_limiters[key]
                # 简单的过期检查，实际可以更复杂
                if hasattr(limiter, 'last_refill') and now - limiter.last_refill > 3600:
                    del user_limiters[key]
            
            if not user_limiters:
                del self.user_limiters[user_id]
        
        # 清理IP限流器
        for ip in list(self.ip_limiters.keys()):
            ip_limiters = self.ip_limiters[ip]
            for key in list(ip_limiters.keys()):
                limiter = ip_limiters[key]
                if hasattr(limiter, 'last_refill') and now - limiter.last_refill > 3600:
                    del ip_limiters[key]
            
            if not ip_limiters:
                del self.ip_limiters[ip]


# 全局限流器实例
rate_limiter = RateLimiter()


def get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
    # 检查代理头部
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    
    # 回退到连接IP
    return request.client.host if request.client else "unknown"


def get_endpoint_category(path: str, method: str) -> str:
    """根据路径和方法确定端点类别"""
    if "/chat/" in path:
        if "/stream" in path:
            return "chat_stream"
        elif "/messages" in path and method == "POST":
            return "chat_message"
        elif "/search/" in path:
            return "search"
        else:
            return "chat_message"
    elif "/conversations" in path and method == "POST":
        return "conversation_create"
    elif "/agents" in path:
        return "agent_management"
    elif "/search" in path:
        return "search"
    else:
        return "global"


async def rate_limit_middleware(request: Request, call_next, user_id: Optional[str] = None):
    """
    FastAPI限流中间件
    
    Args:
        request: FastAPI请求对象
        call_next: 下一个中间件/处理器
        user_id: 用户ID（可选，从认证中间件传递）
    """
    try:
        # 获取客户端信息
        ip_address = get_client_ip(request)
        endpoint_category = get_endpoint_category(request.url.path, request.method)
        
        # 执行限流检查
        result = rate_limiter.check_rate_limit(
            endpoint=endpoint_category,
            user_id=user_id,
            ip_address=ip_address
        )
        
        # 记录限流信息
        logger.debug(f"Rate limit check: endpoint={endpoint_category}, user={user_id}, "
                    f"ip={ip_address}, allowed={result.allowed}, remaining={result.remaining}")
        
        if not result.allowed:
            # 返回限流错误
            logger.warning(f"Rate limit exceeded: endpoint={endpoint_category}, user={user_id}, "
                          f"ip={ip_address}, retry_after={result.retry_after}")
            
            headers = {
                "X-RateLimit-Limit": str(rate_limiter.default_rules.get(endpoint_category, 
                                                                       rate_limiter.default_rules["global"]).requests_per_window),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(result.reset_time)),
                "Retry-After": str(result.retry_after)
            }
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "code": 429,
                    "message": "请求过于频繁，请稍后再试",
                    "error": {
                        "type": "RateLimitExceeded",
                        "details": f"超出速率限制，请在 {result.retry_after} 秒后重试"
                    },
                    "timestamp": datetime.now().isoformat()
                },
                headers=headers
            )
        
        # 执行请求
        response = await call_next(request)
        
        # 添加限流信息到响应头
        rule = rate_limiter.default_rules.get(endpoint_category, rate_limiter.default_rules["global"])
        response.headers["X-RateLimit-Limit"] = str(rule.requests_per_window)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-RateLimit-Reset"] = str(int(result.reset_time))
        
        return response
        
    except Exception as e:
        logger.error(f"Rate limiting middleware error: {e}")
        # 出错时允许请求通过，避免阻塞服务
        return await call_next(request)


# 定期清理任务
async def cleanup_task():
    """定期清理过期的限流器实例"""
    while True:
        try:
            await asyncio.sleep(300)  # 每5分钟清理一次
            rate_limiter.cleanup_expired_limiters()
            logger.debug("Rate limiter cleanup completed")
        except Exception as e:
            logger.error(f"Rate limiter cleanup error: {e}")


# 便捷装饰器
def rate_limit(endpoint: str, custom_rule: Optional[RateLimitRule] = None):
    """
    限流装饰器
    
    Args:
        endpoint: 端点类别
        custom_rule: 自定义限流规则
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 从参数中提取Request对象
            request = None
            user_id = None
            
            # 检查args中的Request对象
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            # 检查kwargs中的Request对象
            if request is None:
                for key, value in kwargs.items():
                    if isinstance(value, Request):
                        request = value
                        break
            
            # 如果没找到Request对象，尝试从函数参数中获取
            if request is None:
                # 获取函数签名
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                
                # 查找Request类型的参数
                for param_name, param_value in bound_args.arguments.items():
                    if isinstance(param_value, Request):
                        request = param_value
                        break
            
            if request is None:
                # 如果还是没找到Request，可能是依赖注入的情况，跳过限流检查
                return await func(*args, **kwargs)
            
            # 尝试从kwargs中获取用户信息
            current_user = kwargs.get('current_user')
            if current_user and hasattr(current_user, 'get'):
                user_id = str(current_user.get('user_id', ''))
            elif current_user and isinstance(current_user, dict):
                user_id = str(current_user.get('user_id', ''))
            
            # 执行限流检查
            ip_address = get_client_ip(request)
            result = rate_limiter.check_rate_limit(
                endpoint=endpoint,
                user_id=user_id,
                ip_address=ip_address,
                custom_rule=custom_rule
            )
            
            if not result.allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "message": "请求过于频繁，请稍后再试",
                        "retry_after": result.retry_after
                    }
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator