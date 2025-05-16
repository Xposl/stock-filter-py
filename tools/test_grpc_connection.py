import grpc
import os
import sys
import logging
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

def test_grpc_connection():
    """测试gRPC服务连接"""
    # 直接从环境变量中获取值并去除任何注释
    auth_host = os.getenv('AUTH_SERVICE_HOST', 'localhost').split('#')[0].strip()
    auth_port = os.getenv('AUTH_SERVICE_PORT', '9091').split('#')[0].strip()
    
    logger.info(f"测试连接到gRPC服务: {auth_host}:{auth_port}")
    
    try:
        # 创建一个不安全的通道
        options = [
            ('grpc.keepalive_time_ms', 10000),
            ('grpc.keepalive_timeout_ms', 5000),
            ('grpc.keepalive_permit_without_calls', 1),
        ]
        channel = grpc.insecure_channel(f"{auth_host}:{auth_port}", options=options)
        
        # 尝试连接，设置5秒超时
        logger.info("尝试连接...")
        grpc.channel_ready_future(channel).result(timeout=5)
        logger.info("✅ 连接成功!")
        
        # gRPC Python客户端库不同版本API可能不同，尝试获取通道状态
        try:
            state = channel.get_state(try_to_connect=True)
            logger.info(f"通道状态: {state}")
        except AttributeError:
            logger.info("此版本的gRPC不支持get_state方法，但连接已确认成功")
        
        try:
            # 尝试导入并使用auth_client
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from core.auth.auth_grpc_client import auth_client
            logger.info("auth_client 导入成功")
            
            # 尝试获取用户信息（使用无效token测试）
            logger.info("尝试调用get_current_user方法(预期失败，因为使用了无效token)")
            result = auth_client.get_current_user("test_token")
            logger.info(f"调用结果: {result}")
            
        except ImportError as ie:
            logger.error(f"导入auth_client失败: {str(ie)}")
        except Exception as e:
            logger.error(f"使用auth_client时出错: {str(e)}")
            
    except grpc.FutureTimeoutError:
        logger.error(f"❌ 连接超时! 请检查服务器地址和端口是否正确，以及服务是否运行")
    except Exception as e:
        logger.error(f"❌ 连接失败: {str(e)}")

if __name__ == "__main__":
    test_grpc_connection()
