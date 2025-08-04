"""
gRPC认证客户端
支持单例模式直连和Nacos服务发现两种连接模式
"""

import grpc
import asyncio
import logging
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from enum import Enum

from app.config import get_settings

# 导入生成的gRPC代码
from app.grpc import auth_pb2, auth_pb2_grpc
from app.grpc.auth.CurrentUser_pb2 import UserRequest, CurrentUser
from app.grpc.auth.CurrentUser_pb2_grpc import CurrentUserServiceStub

logger = logging.getLogger(__name__)


class AuthConnectionMode(Enum):
    """认证连接模式"""
    SINGLETON = "singleton"  # 单例模式直连
    NACOS = "nacos"         # Nacos服务发现


@dataclass
class AuthConfig:
    """认证配置"""
    mode: AuthConnectionMode
    
    # 单例模式配置
    auth_host: Optional[str] = None
    auth_port: int = 9091
    
    # Nacos模式配置
    nacos_server: Optional[str] = None
    nacos_namespace: str = "public"
    service_name: str = "auth-service"
    
    # 通用配置
    timeout: int = 30
    max_retry: int = 3
    
    @classmethod
    def from_settings(cls) -> 'AuthConfig':
        """从统一配置创建认证配置"""
        settings = get_settings()
        
        # 确定连接模式：如果启用了nacos则使用nacos模式，否则使用单例模式
        mode = AuthConnectionMode.NACOS if settings.nacos_enabled else AuthConnectionMode.SINGLETON
        
        config = cls(mode=mode)
        
        if mode == AuthConnectionMode.SINGLETON:
            config.auth_host = settings.auth_service_host
            config.auth_port = settings.auth_service_port
        else:
            config.nacos_server = settings.nacos_server_url
            config.nacos_namespace = settings.nacos_namespace
            config.service_name = settings.auth_service_name
        
        config.timeout = settings.auth_timeout
        config.max_retry = settings.auth_retry_max
        
        return config


class GrpcAuthClient:
    """简化的gRPC认证客户端"""
    
    def __init__(self, config: Optional[AuthConfig] = None):
        self.config = config or AuthConfig.from_settings()
        self.channel: Optional[grpc.aio.Channel] = None
        self.auth_stub: Optional[auth_pb2_grpc.AuthServiceStub] = None
        self.current_user_stub: Optional[CurrentUserServiceStub] = None
        self.nacos_client: Optional = None  # 暂时不导入nacos，避免依赖问题
        self._connected = False
        
    async def connect(self) -> bool:
        """建立连接"""
        try:
            if self.config.mode == AuthConnectionMode.SINGLETON:
                await self._connect_singleton()
            else:
                await self._connect_nacos()
            
            self._connected = True
            logger.info(f"gRPC认证客户端连接成功，模式: {self.config.mode.value}")
            return True
            
        except Exception as e:
            logger.error(f"gRPC认证客户端连接失败: {e}")
            return False
    
    async def _connect_singleton(self):
        """单例模式直连"""
        address = f"{self.config.auth_host}:{self.config.auth_port}"
        self.channel = grpc.aio.insecure_channel(address)
        
        # 创建服务桩
        self.auth_stub = auth_pb2_grpc.AuthServiceStub(self.channel)
        self.current_user_stub = CurrentUserServiceStub(self.channel)
        
        logger.info(f"使用单例模式连接到认证服务: {address}")
    
    async def _connect_nacos(self):
        """Nacos服务发现模式"""
        # 只有在nacos_enabled时才尝试导入nacos
        try:
            import nacos
            
            # 初始化Nacos客户端
            self.nacos_client = nacos.NacosClient(
                self.config.nacos_server,
                namespace=self.config.nacos_namespace
            )
            
            # 发现服务实例
            instances = self.nacos_client.list_naming_instance(
                self.config.service_name,
                healthy_only=True
            )
            
            if not instances:
                raise Exception(f"未发现健康的认证服务实例: {self.config.service_name}")
            
            # 选择第一个健康实例（单例模式）
            instance = instances[0]
            address = f"{instance['ip']}:{instance['port']}"
            
            self.channel = grpc.aio.insecure_channel(address)
            self.auth_stub = auth_pb2_grpc.AuthServiceStub(self.channel)
            self.current_user_stub = CurrentUserServiceStub(self.channel)
            
            logger.info(f"通过Nacos发现认证服务: {address}")
            
        except ImportError:
            logger.error("Nacos模式需要安装nacos-sdk-python: pip install nacos-sdk-python")
            raise
    
    async def validate_token(self, token: str, service_name: str = "agent-system") -> Optional[Dict[str, Any]]:
        """验证Token"""
        if not self._connected:
            await self.connect()
        
        try:
            request = auth_pb2.TokenValidationRequest(
                token=token,
                service_name=service_name
            )
            
            response = await self.auth_stub.ValidateToken(request, timeout=self.config.timeout)
            
            if response.valid:
                user_info = {
                    "user_id": response.user_info.user_id,
                    "username": response.user_info.username,
                    "email": response.user_info.email,
                    "platform_id": response.user_info.platform_id,
                    "roles": list(response.user_info.roles),
                    "expires_at": response.expires_at
                }
                return user_info
            else:
                logger.warning(f"Token验证失败: {response.message}")
                return None
                
        except grpc.RpcError as e:
            logger.error(f"gRPC调用失败: {e}")
            return None
    
    async def authenticate(self, token: str, service_name: str = "agent-system", 
                          permissions: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """完整认证（包含权限检查）"""
        if not self._connected:
            await self.connect()
        
        try:
            request = auth_pb2.AuthRequest(
                token=token,
                service_name=service_name,
                required_permissions=permissions or []
            )
            
            response = await self.auth_stub.Authenticate(request, timeout=self.config.timeout)
            
            if response.success:
                return {
                    "success": True,
                    "user_info": {
                        "user_id": response.user_info.user_id,
                        "username": response.user_info.username,
                        "platform_id": response.user_info.platform_id,
                        "roles": list(response.user_info.roles)
                    },
                    "granted_permissions": list(response.granted_permissions)
                }
            else:
                logger.warning(f"认证失败: {response.message}")
                return {"success": False, "message": response.message}
                
        except grpc.RpcError as e:
            logger.error(f"gRPC认证调用失败: {e}")
            return None
    
    async def get_current_user(self, token: str) -> Optional[Dict[str, Any]]:
        """获取当前用户信息（使用CurrentUserService）"""
        if not self._connected:
            await self.connect()
        
        try:
            request = UserRequest(token=token)
            response = await self.current_user_stub.GetCurrentUser(request, timeout=self.config.timeout)
            
            user_data = {
                "user_id": response.user_id,
                "username": response.username,
                "email": response.email,
                "nickname": response.nickname,
                "avatar": response.avatar,
                "platform_id": response.platform_id,
                "client_id": response.client_id,
                "roles": list(response.roles),
                "authorities": list(response.authorities),
                "super_admin": response.super_admin,
                "metadata": dict(response.metadata)
            }
            
            return user_data
            
        except grpc.RpcError as e:
            logger.error(f"获取用户信息失败: {e}")
            return None
    
    async def close(self):
        """关闭连接"""
        if self.channel:
            await self.channel.close()
            self._connected = False
            logger.info("gRPC认证客户端连接已关闭")


# 全局实例
_grpc_auth_client: Optional[GrpcAuthClient] = None


def get_auth_client() -> GrpcAuthClient:
    """获取gRPC认证客户端实例"""
    global _grpc_auth_client
    if _grpc_auth_client is None:
        _grpc_auth_client = GrpcAuthClient()
    return _grpc_auth_client


async def cleanup_auth_client():
    """清理gRPC认证客户端"""
    global _grpc_auth_client
    if _grpc_auth_client:
        await _grpc_auth_client.close()
    _grpc_auth_client = None 


def get_dummy_user_info() -> Dict[str, Any]:
    """获取虚拟用户信息"""
    return {
        "user_id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "platform_id": "0",
        "roles": ["admin"],
    }