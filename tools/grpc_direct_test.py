import grpc
import os
import logging
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

def test_direct_connection():
    """测试直接连接到gRPC服务器"""
    try:
        host = "47.107.28.9"
        port = "9091"
        logger.info(f"尝试直接连接到 {host}:{port}")
        
        # 创建grpc通道
        channel = grpc.insecure_channel(f"{host}:{port}")
        logger.info("通道创建成功，尝试建立连接...")
        
        # 尝试连接
        try:
            grpc.channel_ready_future(channel).result(timeout=5)
            logger.info("✅ 连接成功!")
        except grpc.FutureTimeoutError:
            logger.error("❌ 连接超时!")
        except Exception as e:
            logger.error(f"❌ 连接失败: {e}")
            
    except Exception as e:
        logger.error(f"发生错误: {e}")

if __name__ == "__main__":
    test_direct_connection()
