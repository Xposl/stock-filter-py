"""
调试认证客户端连接问题
"""
import os
import sys
import logging
import grpc
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
load_dotenv()

def debug_auth_client():
    """调试认证客户端"""
    # 测试直接连接
    auth_host = os.getenv('AUTH_SERVICE_HOST', 'localhost').split('#')[0].strip()
    auth_port = os.getenv('AUTH_SERVICE_PORT', '9091').split('#')[0].strip()
    
    logger.info(f"测试直接连接 gRPC 服务: {auth_host}:{auth_port}")
    
    try:
        # 尝试直接连接
        channel = grpc.insecure_channel(f"{auth_host}:{auth_port}")
        try:
            grpc.channel_ready_future(channel).result(timeout=5)
            logger.info("✅ 直接连接成功!")
        except grpc.FutureTimeoutError:
            logger.error("❌ 直接连接超时!")
        except Exception as e:
            logger.error(f"❌ 直接连接失败: {str(e)}")
    except Exception as e:
        logger.error(f"❌ 创建channel失败: {str(e)}")
    
    # 测试auth_client
    try:
        from core.auth.auth_grpc_client import auth_client
        logger.info("导入 auth_client 成功")
        
        # 测试获取通道
        try:
            logger.info("测试 auth_client._get_channel()")
            channel = auth_client._get_channel()
            logger.info("✅ 获取通道成功")
        except Exception as e:
            logger.error(f"❌ 获取通道失败: {str(e)}")
        
        # 测试获取当前用户
        try:
            token = "测试Token"  # 使用一个无效的token来测试连接
            logger.info(f"测试 auth_client.get_current_user() 使用token: {token}")
            result = auth_client.get_current_user(token)
            if result is None:
                logger.info("✅ 预期结果: 无权限访问 (None)")
            else:
                logger.info(f"意外结果: {result}")
        except Exception as e:
            logger.error(f"❌ 调用 get_current_user 失败: {str(e)}")
            
    except ImportError as e:
        logger.error(f"❌ 导入 auth_client 失败: {str(e)}")
    except Exception as e:
        logger.error(f"❌ 使用 auth_client 时出错: {str(e)}")

if __name__ == "__main__":
    debug_auth_client()
