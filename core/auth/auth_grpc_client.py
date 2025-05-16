import os
import grpc
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List

# 当生成gRPC代码后，导入相关服务
try:
    # 导入生成的 gRPC 代码
    from core.grpc.auth.CurrentUser_pb2_grpc import CurrentUserServiceStub
    from core.grpc.auth.UserAccount_pb2_grpc import UserAccountServiceStub
    from core.grpc.auth.CurrentUser_pb2 import UserRequest
except ImportError as e:
    # 如果还没有生成gRPC代码，这些导入会失败
    print(f"ImportError: {str(e)}")
    print("警告: gRPC代码尚未生成，请先运行 tools/generate_grpc_code.py")

# 加载环境变量
load_dotenv()

# 鉴权服务的地址，默认使用提供的服务地址
AUTH_SERVICE_HOST = os.getenv('AUTH_SERVICE_HOST', 'localhost').split('#')[0].strip()
AUTH_SERVICE_PORT = os.getenv('AUTH_SERVICE_PORT', '9091').split('#')[0].strip()

class AuthGrpcClient:
    """鉴权服务gRPC客户端"""
    
    def __init__(self):
        self.channel = None
        self._current_user_stub = None
        self._user_account_stub = None
    
    def _get_channel(self):
        """获取或创建gRPC通道"""
        import logging
        logger = logging.getLogger(__name__)
        
        connected = False
        try_count = 0
        max_retries = 3
        
        while not connected and try_count < max_retries:
            try:
                if not self.channel:
                    logger.info(f"尝试连接gRPC认证服务: {AUTH_SERVICE_HOST}:{AUTH_SERVICE_PORT}")
                    
                    # 设置连接超时选项
                    options = [
                        ('grpc.keepalive_time_ms', 10000),
                        ('grpc.keepalive_timeout_ms', 5000),
                        ('grpc.keepalive_permit_without_calls', 1),
                        ('grpc.http2.max_pings_without_data', 0),
                    ]
                    self.channel = grpc.insecure_channel(f"{AUTH_SERVICE_HOST}:{AUTH_SERVICE_PORT}", options=options)
                
                # 测试连接
                grpc.channel_ready_future(self.channel).result(timeout=5)
                logger.info("gRPC认证服务连接成功")
                connected = True
            except grpc.FutureTimeoutError:
                try_count += 1
                logger.warning(f"无法连接到gRPC认证服务: {AUTH_SERVICE_HOST}:{AUTH_SERVICE_PORT} - 连接超时 (尝试 {try_count}/{max_retries})")
                if try_count >= max_retries:
                    logger.error("已达到最大重试次数，无法连接到认证服务")
                    # 返回当前通道而不抛出异常，调用者将处理连接错误
                self.channel = None
            except Exception as e:
                try_count += 1
                logger.warning(f"gRPC通道创建失败: {str(e)} (尝试 {try_count}/{max_retries})")
                if try_count >= max_retries:
                    logger.error("已达到最大重试次数，无法创建gRPC通道")
                    # 返回当前通道而不抛出异常，调用者将处理连接错误
                self.channel = None
                
        return self.channel
    
    @property
    def current_user_stub(self):
        """获取CurrentUserServiceStub"""
        if not self._current_user_stub:
            self._current_user_stub = CurrentUserServiceStub(self._get_channel())
        return self._current_user_stub
    
    @property
    def user_account_stub(self):
        """获取UserAccountServiceStub"""
        if not self._user_account_stub:
            self._user_account_stub = UserAccountServiceStub(self._get_channel())
        return self._user_account_stub
    
    def get_current_user(self, token: str) -> Optional[Dict[str, Any]]:
        """
        获取当前用户信息
        
        Args:
            token: 认证token
        
        Returns:
            用户信息字典或None（如果认证失败）
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # 创建请求
            logger.debug("正在准备用户认证请求")
            request = UserRequest(token=token)
            
            # 设置元数据和超时时间
            metadata = [('token', token)]
            # 调用远程服务，设置10秒超时
            logger.debug("正在调用gRPC认证服务")
            response = self.current_user_stub.queryCurrentUser(
                request, 
                metadata=metadata,
                timeout=10.0
            )
            
            # 转换为Python字典
            if response and response.user:
                logger.debug("成功获取用户信息")
                user = {
                    'id': response.user.id,
                    'unionId': response.user.unionId,
                    'userNo': response.user.userNo,
                    'userName': response.user.userName,
                    'nickName': response.user.nickName,
                    'avatar': response.user.avatar,
                    'superAdmin': response.user.superAdmin,
                    'authUser': response.user.authUser,
                    'tenantId': response.user.tenantId,
                    'createTime': response.user.createTime
                }
                
                # 添加权限信息
                authorities = list(response.authorities) if response.authorities else []
                
                return {
                    'user': user,
                    'clientId': response.clientId,
                    'authorities': authorities
                }
            
            logger.warning("gRPC服务返回了空的用户信息")
            return None
        except grpc.RpcError as e:
            logger.error(f"gRPC错误: {e.code()}, {e.details()}")
            # 记录更多详细信息，以便诊断
            if e.code() == grpc.StatusCode.UNAVAILABLE:
                logger.error(f"无法连接到认证服务 {AUTH_SERVICE_HOST}:{AUTH_SERVICE_PORT}，请检查服务是否运行")
            elif e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                logger.error("认证服务响应超时")
            elif e.code() == grpc.StatusCode.UNAUTHENTICATED:
                logger.warning("提供的认证Token无效")
            return None
        except Exception as e:
            logger.error(f"获取用户信息时发生错误: {str(e)}", exc_info=True)
            return None

    def close(self):
        """关闭gRPC通道"""
        if self.channel:
            self.channel.close()
            self.channel = None
            self._current_user_stub = None
            self._user_account_stub = None

# 创建单例实例
auth_client = AuthGrpcClient()
