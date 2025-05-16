"""
检查令牌授权信息
"""
import sys
import os
import logging
import argparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_token_auth(token):
    """测试Token的授权信息"""
    try:
        from core.auth.auth_grpc_client import auth_client
        
        logger.info(f"正在检查Token权限: {token[:8]}...")
        user_info = auth_client.get_current_user(token)
        
        if not user_info:
            logger.error("❌ 无效的Token或认证服务不可用")
            return
            
        # 打印用户信息和权限
        logger.info("✅ 获取用户信息成功:")
        logger.info(f"用户名: {user_info.get('user', {}).get('userName', 'N/A')}")
        logger.info(f"昵称: {user_info.get('user', {}).get('nickName', 'N/A')}")
        logger.info(f"是否超级管理员: {user_info.get('user', {}).get('superAdmin', False)}")
        logger.info(f"客户端ID: {user_info.get('clientId', 'N/A')}")
        
        # 打印权限列表  
        authorities = user_info.get("authorities", [])
        logger.info(f"拥有的权限 ({len(authorities)}):")
        for auth in authorities:
            logger.info(f"  - {auth}")
            
        # 检查是否有ADMIN权限
        if "ADMIN" in authorities:
            logger.info("✅ 用户拥有ADMIN权限，可访问定时任务API")
        else:
            logger.warning("⚠️ 用户没有ADMIN权限，无法访问定时任务API")
            
    except Exception as e:
        logger.error(f"❌ 检查权限时出错: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='检查Token的授权信息')
    parser.add_argument('token', help='要检查的认证Token')
    
    args = parser.parse_args()
    check_token_auth(args.token)
