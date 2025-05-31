#!/usr/bin/env python3
# filepath: /Users/xposl/Workspace/me/InvestNote-py/tools/test_auth_service.py
"""
测试鉴权服务连接和功能
"""
import os
import sys
import argparse
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 加载环境变量
load_dotenv()

def test_auth_connection(token=None):
    """
    测试鉴权服务连接
    
    Args:
        token: 用于测试的认证token
    """
    try:
        # 尝试导入gRPC客户端
        from core.auth.auth_grpc_client import auth_client
        
        print("✅ 成功导入鉴权客户端")
        
        # 如果提供了token，尝试获取用户信息
        if token:
            print(f"正在使用token获取用户信息...(token前6位: {token[:6]}***)")
            user_info = auth_client.get_current_user(token)
            
            if user_info:
                print("✅ 成功获取用户信息:")
                print(f"  - 用户ID: {user_info['user']['id']}")
                print(f"  - 用户名: {user_info['user']['userName'] or user_info['user']['nickName']}")
                print(f"  - 客户端ID: {user_info['clientId']}")
                print(f"  - 权限: {', '.join(user_info['authorities']) if user_info['authorities'] else '无'}")
                return True
            else:
                print("❌ 获取用户信息失败，请检查Token是否有效")
                return False
        else:
            print("未提供测试Token，跳过用户信息测试")
            return True
            
    except ImportError as e:
        print(f"❌ 导入错误: {str(e)}")
        print("请先运行 python tools/generate_grpc_code.py 生成gRPC代码")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="测试鉴权服务")
    parser.add_argument("--token", help="用于测试的认证token")
    args = parser.parse_args()
    
    success = test_auth_connection(args.token)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
