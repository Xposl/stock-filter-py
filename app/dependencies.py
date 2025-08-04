"""
FastAPI依赖注入配置
基于简化的gRPC认证系统
"""

import logging
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.auth_service import get_auth_service, UserInfo
from app.services.database_service import get_database_service
from app.memory.service import get_memory_service
from app.services.multi_model_service import get_multi_model_service
from app.auth.auth_middleware import get_current_user, verify_bearer_token

logger = logging.getLogger(__name__)

# HTTP Bearer scheme
security = HTTPBearer(auto_error=False)


# === 认证相关依赖 ===

async def get_current_user_from_request(request: Request) -> UserInfo:
    """从请求获取当前用户信息（中间件注入）"""
    return await get_current_user(request)


async def get_current_user_from_token(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)]
) -> UserInfo:
    """从Token获取当前用户信息（依赖注入方式）"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证凭据",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    authorization = f"Bearer {credentials.credentials}"
    return await verify_bearer_token(authorization)


async def get_optional_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)]
) -> Optional[UserInfo]:
    """可选用户认证（允许匿名访问）"""
    if not credentials:
        return None
    
    try:
        authorization = f"Bearer {credentials.credentials}"
        return await verify_bearer_token(authorization)
    except HTTPException:
        # 认证失败但允许匿名访问
        return None


def require_permissions(*permissions: str):
    """需要特定权限的依赖"""
    async def check_permissions(user: UserInfo = Depends(get_current_user_from_token)) -> UserInfo:
        auth_service = get_auth_service()
        
        for permission in permissions:
            has_permission = await auth_service.check_permission(user.user_id, permission)
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"缺少权限: {permission}"
                )
        
        return user
    
    return check_permissions


# === 业务服务依赖 ===

def get_auth_service_dependency():
    """获取认证服务依赖"""
    return get_auth_service()


def get_database_service_dependency():
    """获取数据库服务依赖"""
    return get_database_service()


def get_memory_service_dependency():
    """获取记忆服务依赖"""
    return get_memory_service()


def get_multi_model_service_dependency():
    """获取多模型服务依赖"""
    return get_multi_model_service()


# === 类型注解别名 ===

# 当前用户（必须认证）
CurrentUser = Annotated[UserInfo, Depends(get_current_user_from_token)]

# 可选用户（允许匿名）
OptionalUser = Annotated[Optional[UserInfo], Depends(get_optional_user)]

# 从请求中获取用户（需要中间件）
RequestUser = Annotated[UserInfo, Depends(get_current_user_from_request)]

# 业务服务依赖
AuthService = Annotated[type, Depends(get_auth_service_dependency)]
DatabaseService = Annotated[type, Depends(get_database_service_dependency)]
MemoryService = Annotated[type, Depends(get_memory_service_dependency)]
MultiModelService = Annotated[type, Depends(get_multi_model_service_dependency)]



