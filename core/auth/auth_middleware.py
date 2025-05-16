from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List, Dict, Any, Callable, Union

from .auth_grpc_client import auth_client

# 创建HTTP Bearer标准验证器
security = HTTPBearer(auto_error=False)

class AuthDependency:
    """
    身份验证依赖项
    
    用法:
        @app.get("/protected")
        async def protected_route(current_user: dict = Depends(auth_required())):
            return {"message": "您已通过认证", "user": current_user}
            
        @app.get("/admin-only")
        async def admin_route(current_user: dict = Depends(auth_required(["ADMIN"]))):
            return {"message": "您是管理员", "user": current_user}
    """
    
    def __init__(self, required_authorities: Optional[List[str]] = None):
        """
        初始化身份验证依赖
        
        Args:
            required_authorities: 需要的权限列表，如果为None则只要求用户已认证
        """
        self.required_authorities = required_authorities or []
    
    async def __call__(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
        """
        验证用户并返回用户信息
        
        Args:
            credentials: 认证凭据
            
        Returns:
            用户信息字典
            
        Raises:
            HTTPException: 认证失败或权限不足时抛出异常
        """
        if not credentials:
            raise HTTPException(
                status_code=401,
                detail="未提供认证信息",
                headers={"WWW-Authenticate": "Bearer"}
            )
            
        # 获取token
        token = credentials.credentials
        if not token:
            raise HTTPException(
                status_code=401,
                detail="未提供有效的认证token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # 通过gRPC获取用户信息
        user_info = auth_client.get_current_user(token)
        if not user_info:
            raise HTTPException(
                status_code=401,
                detail="无效的认证token或认证服务暂不可用",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # 检查所需权限
        if self.required_authorities:
            user_authorities = user_info.get("authorities", [])
            # 检查用户是否具有所需的任意一个权限
            if not any(auth in user_authorities for auth in self.required_authorities):
                raise HTTPException(
                    status_code=403,
                    detail="权限不足，无法访问此资源"
                )
        
        return user_info

def auth_required(required_authorities: Optional[List[str]] = None) -> Callable:
    """
    要求认证的依赖函数
    
    Args:
        required_authorities: 需要的权限列表，如果为None则只要求用户已认证
    
    Returns:
        依赖函数
    """
    return AuthDependency(required_authorities)
