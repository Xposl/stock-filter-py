import os
import grpc
from dotenv import load_dotenv
from typing import Optional, Dict, Any, List
import logging
import threading

# 在导入gRPC之前设置环境变量以抑制警告
os.environ.setdefault('GRPC_VERBOSITY', 'ERROR')
os.environ.setdefault('GRPC_TRACE', '')

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
        self._lock = threading.Lock()
        self._initialized = False
    
    def _get_channel(self):
        """获取或创建gRPC通道"""
        logger = logging.getLogger(__name__)
        
        # 使用双重检查锁定确保线程安全的延迟初始化
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._initialize_connection()
                    self._initialized = True
        
        return self.channel
    
    def _initialize_connection(self):
        """初始化gRPC连接（内部方法，线程安全）"""
        logger = logging.getLogger(__name__)
        
        try:
            logger.debug(f"初始化gRPC认证服务连接: {AUTH_SERVICE_HOST}:{AUTH_SERVICE_PORT}")
            
            # 设置连接选项，包括fork安全选项
            options = [
                ('grpc.keepalive_time_ms', 10000),
                ('grpc.keepalive_timeout_ms', 5000),
                ('grpc.keepalive_permit_without_calls', 1),
                ('grpc.http2.max_pings_without_data', 0),
                ('grpc.max_receive_message_length', 4 * 1024 * 1024),  # 4MB
                ('grpc.max_send_message_length', 4 * 1024 * 1024),     # 4MB
                # 添加fork安全选项
                ('grpc.enable_retries', 0),
            ]
            
            self.channel = grpc.insecure_channel(
                f"{AUTH_SERVICE_HOST}:{AUTH_SERVICE_PORT}", 
                options=options
            )
            
            logger.debug("gRPC通道创建成功")
            
        except Exception as e:
            logger.error(f"gRPC通道创建失败: {str(e)}")
            self.channel = None
            raise
    
    def test_connection(self, timeout: float = 5.0) -> bool:
        """测试gRPC连接"""
        logger = logging.getLogger(__name__)
        
        try:
            if not self.channel:
                self._get_channel()
            
            if self.channel:
                # 测试连接
                grpc.channel_ready_future(self.channel).result(timeout=timeout)
                logger.debug("gRPC连接测试成功")
                return True
            else:
                logger.warning("gRPC通道未初始化")
                return False
                
        except grpc.FutureTimeoutError:
            logger.warning(f"gRPC连接测试超时 ({timeout}s)")
            return False
        except Exception as e:
            logger.warning(f"gRPC连接测试失败: {str(e)}")
            return False
    
    @property
    def current_user_stub(self):
        """获取CurrentUserServiceStub"""
        if not self._current_user_stub:
            channel = self._get_channel()
            if channel:
                self._current_user_stub = CurrentUserServiceStub(channel)
        return self._current_user_stub
    
    @property
    def user_account_stub(self):
        """获取UserAccountServiceStub"""
        if not self._user_account_stub:
            channel = self._get_channel()
            if channel:
                self._user_account_stub = UserAccountServiceStub(channel)
        return self._user_account_stub
    
    def get_current_user(self, token: str) -> Optional[Dict[str, Any]]:
        """
        获取当前用户信息
        
        Args:
            token: 认证token
        
        Returns:
            用户信息字典或None（如果认证失败）
        """
        logger = logging.getLogger(__name__)
        
        try:
            # 延迟初始化：只有在实际使用时才建立连接
            stub = self.current_user_stub
            if not stub:
                logger.error("无法获取gRPC stub，连接可能失败")
                return None
            
            # 创建请求
            logger.debug("正在准备用户认证请求")
            request = UserRequest(token=token)
            
            # 设置元数据和超时时间
            metadata = [('token', token)]
            # 调用远程服务，设置10秒超时
            logger.debug("正在调用gRPC认证服务")
            response = stub.queryCurrentUser(
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
        with self._lock:
            if self.channel:
                try:
                    self.channel.close()
                except Exception as e:
                    logging.getLogger(__name__).warning(f"关闭gRPC通道时发生错误: {e}")
                finally:
                    self.channel = None
                    self._current_user_stub = None
                    self._user_account_stub = None
                    self._initialized = False

# 创建单例实例（但不立即初始化连接）
auth_client = AuthGrpcClient()
