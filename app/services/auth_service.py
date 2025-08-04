"""
简化的认证服务
支持gRPC认证和测试模式
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

from app.config import get_settings
from app.auth.grpc_auth_client import get_auth_client, GrpcAuthClient

logger = logging.getLogger(__name__)


@dataclass
class UserInfo:
    """用户信息"""
    user_id: str
    username: str
    email: Optional[str] = None
    platform_id: Optional[str] = None
    roles: list = None
    authorities: list = None
    super_admin: bool = False
    
    def __post_init__(self):
        if self.roles is None:
            self.roles = []
        if self.authorities is None:
            self.authorities = []


class AuthService:
    """认证服务"""
    
    def __init__(self):
        settings = get_settings()
        self.test_mode = settings.test_mode
        self.grpc_client: Optional[GrpcAuthClient] = None
        
        if not self.test_mode:
            self.grpc_client = get_auth_client()
    
    async def authenticate_token(self, token: str) -> Optional[UserInfo]:
        """认证Token并返回用户信息"""
        
        # 测试模式
        if self.test_mode:
            logger.info("使用测试模式认证")
            settings = get_settings()
            return UserInfo(
                user_id=settings.test_user_id,
                username=settings.test_username,
                email=f"{settings.test_username}@test.local",
                platform_id="test_platform",
                roles=["USER", "ADMIN"],
                authorities=["READ", "WRITE", "ADMIN"],
                super_admin=True
            )
        
        # 生产模式 - gRPC认证
        if not token:
            logger.warning("Token为空")
            return None
        
        if not token.startswith('Bearer '):
            logger.warning("Token格式不正确，应该以'Bearer '开头")
            return None
        
        # 提取实际token
        actual_token = token[7:]  # 移除 'Bearer ' 前缀
        
        try:
            # 优先使用CurrentUserService获取用户信息
            user_data = await self.grpc_client.get_current_user(actual_token)
            
            if user_data:
                return UserInfo(
                    user_id=str(user_data.get('user_id', '')),
                    username=user_data.get('username', ''),
                    email=user_data.get('email', ''),
                    platform_id=user_data.get('platform_id', ''),
                    roles=user_data.get('roles', []),
                    authorities=user_data.get('authorities', []),
                    super_admin=user_data.get('super_admin', False)
                )
            
            # 备用: 使用基础的Token验证
            auth_data = await self.grpc_client.validate_token(actual_token)
            
            if auth_data:
                return UserInfo(
                    user_id=str(auth_data.get('user_id', '')),
                    username=auth_data.get('username', ''),
                    email=auth_data.get('email', ''),
                    platform_id=auth_data.get('platform_id', ''),
                    roles=auth_data.get('roles', [])
                )
            
            logger.warning("Token验证失败")
            return None
            
        except Exception as e:
            logger.error(f"认证过程中发生错误: {e}")
            return None
    
    async def check_permission(self, user_id: str, permission: str) -> bool:
        """检查用户权限"""
        if self.test_mode:
            # 测试模式下允许所有权限
            return True
        
        try:
            # 这里可以实现更复杂的权限检查逻辑
            # 目前简化为检查用户是否存在
            return bool(user_id)
            
        except Exception as e:
            logger.error(f"权限检查失败: {e}")
            return False
    
    async def validate_service_permission(self, token: str, service_name: str, 
                                        permissions: Optional[list] = None) -> Optional[Dict[str, Any]]:
        """验证服务访问权限"""
        if self.test_mode:
            settings = get_settings()
            return {
                "success": True,
                "user_info": {
                    "user_id": settings.test_user_id,
                    "username": settings.test_username,
                    "platform_id": "test_platform"
                },
                "granted_permissions": permissions or []
            }
        
        if not token.startswith('Bearer '):
            return None
        
        actual_token = token[7:]
        
        try:
            return await self.grpc_client.authenticate(
                actual_token, 
                service_name, 
                permissions
            )
        except Exception as e:
            logger.error(f"服务权限验证失败: {e}")
            return None
    
    def is_test_mode(self) -> bool:
        """检查是否为测试模式"""
        return self.test_mode
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        status = {
            "status": "healthy",
            "test_mode": self.test_mode,
            "grpc_connected": False
        }
        
        if not self.test_mode and self.grpc_client:
            try:
                # 尝试连接检查
                connected = await self.grpc_client.connect()
                status["grpc_connected"] = connected
            except Exception as e:
                logger.error(f"gRPC连接检查失败: {e}")
                status["grpc_connected"] = False
                status["status"] = "degraded"
        
        return status


# 全局实例
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """获取认证服务实例"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


async def cleanup_auth_service():
    """清理认证服务"""
    global _auth_service
    if _auth_service and _auth_service.grpc_client:
        await _auth_service.grpc_client.close()
    _auth_service = None
