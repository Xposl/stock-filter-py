"""
鉴权服务相关的gRPC代码包
"""
import os
import sys

# 添加当前目录到Python路径，以便proto生成的代码可以正确导入
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)
