"""
简化的认证中间件
基于gRPC认证服务进行用户认证和权限验证
"""

import logging
from typing import Optional, Callable, Dict, Any
from fastapi import Request, Response, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware

from app.auth.grpc_auth_client import get_dummy_user_info
from app.config import get_settings
from app.services.auth_service import get_auth_service, UserInfo

logger = logging.getLogger(__name__)

# HTTP Bearer Token 提取器
bearer_scheme = HTTPBearer(auto_error=False)


class AuthMiddleware(BaseHTTPMiddleware):
    """可选认证中间件（支持匿名访问）"""
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.auth_service = get_auth_service()
        self.settings = get_settings()
        
        # 使用配置中的排除路径，或者传入的自定义路径
        self.exclude_paths = exclude_paths or self.settings.auth_exclude_paths
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """中间件主要逻辑"""
        
        # 检查是否需要跳过认证
        if self._should_skip_auth(request):
            return await call_next(request)
        
        # 提取Authorization头
        authorization = request.headers.get("authorization")
        
        if authorization:
            try:
                # 尝试认证用户
                user_info = await self.auth_service.authenticate_token(authorization)
                
                if user_info:
                    # 将用户信息注入到请求上下文中
                    request.state.user = user_info
                    request.state.user_id = user_info.user_id
                    request.state.platform_id = user_info.platform_id
                    request.state.authenticated = True
                else:
                    # 认证失败，但允许匿名访问
                    request.state.authenticated = False
                    
            except Exception as e:
                logger.warning(f"可选认证失败: {e}")
                request.state.authenticated = False
        else:
            if  self.settings.auth_enabled is False:
                dummy_user = get_dummy_user_info()
                request.state.user = dummy_user
                request.state.user_id = int(dummy_user["user_id"])
                request.state.platform_id = dummy_user["platform_id"]
                request.state.authenticated = True
                return await call_next(request)
            # 没有Authorization头，匿名访问
            request.state.authenticated = False
        
        return await call_next(request)
    
    def _should_skip_auth(self, request: Request) -> bool:
        """判断是否应该跳过认证"""
        path = request.url.path
        
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True
        
        return False


async def get_current_user(request: Request) -> UserInfo:
    """从请求中获取当前用户信息"""
    if not hasattr(request.state, 'user'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户未认证",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return request.state.user


async def get_current_user_id(
    user: Dict[str, Any] = Depends(get_current_user)
) -> str:
    """获取当前用户ID.

    Args:
        user: 当前用户对象

    Returns:
        用户ID
    """
    return user["user_id"]


async def verify_bearer_token(authorization: str) -> UserInfo:
    """验证Bearer Token并返回用户信息（用于依赖注入）"""
    auth_service = get_auth_service()
    
    user_info = await auth_service.authenticate_token(authorization)
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token验证失败",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user_info


async def require_permission(request: Request, permission: str) -> bool:
    """检查用户权限"""
    user = await get_current_user(request)
    auth_service = get_auth_service()
    
    has_permission = await auth_service.check_permission(user.user_id, permission)
    
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"缺少权限: {permission}"
        )
    
    return True


async def get_current_user_optional(request: Request) -> Optional[UserInfo]:
    """获取当前用户信息（可选，支持匿名）"""
    if hasattr(request.state, 'user') and request.state.authenticated:
        return request.state.user
    return None


def is_authenticated(request: Request) -> bool:
    """检查用户是否已认证"""
    return hasattr(request.state, 'authenticated') and request.state.authenticated
