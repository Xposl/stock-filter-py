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
AUTH_SERVICE_HOST = os.getenv('AUTH_SERVICE_HOST', 'localhost')
AUTH_SERVICE_PORT = os.getenv('AUTH_SERVICE_PORT', '50051')  # 假设gRPC端口为50051

class AuthGrpcClient:
    """鉴权服务gRPC客户端"""
    
    def __init__(self):
        self.channel = None
        self._current_user_stub = None
        self._user_account_stub = None
    
    def _get_channel(self):
        """获取或创建gRPC通道"""
        if not self.channel or self.channel.get_state(try_to_connect=False) == grpc.ChannelConnectivity.SHUTDOWN:
            self.channel = grpc.insecure_channel(f"{AUTH_SERVICE_HOST}:{AUTH_SERVICE_PORT}")
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
        try:
            # 创建请求
            request = UserRequest(token=token)
            # 调用远程服务
            response = self.current_user_stub.queryCurrentUser(request)
            
            # 转换为Python字典
            if response and response.user:
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
            
            return None
        except grpc.RpcError as e:
            print(f"gRPC错误: {e.code()}, {e.details()}")
            return None
        except Exception as e:
            print(f"获取用户信息时发生错误: {str(e)}")
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
