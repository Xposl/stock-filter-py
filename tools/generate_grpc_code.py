#!/usr/bin/env python3
# filepath: /Users/xposl/Workspace/me/InvestNote-py/tools/generate_grpc_code.py
import os
import subprocess

# 项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# proto文件目录
PROTO_DIR = os.path.join(PROJECT_ROOT, "proto")
# 生成的grpc代码存放目录
GRPC_OUT_DIR = os.path.join(PROJECT_ROOT, "core/grpc")

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def generate_grpc_code():
    """生成gRPC代码"""
    ensure_dir(GRPC_OUT_DIR)
    
    # 遍历所有proto文件
    for root, _, files in os.walk(PROTO_DIR):
        for file in files:
            if file.endswith('.proto'):
                proto_file = os.path.join(root, file)
                # 对每个proto文件生成Python代码
                cmd = [
                    'python', '-m', 'grpc_tools.protoc',
                    f'--proto_path={PROTO_DIR}',
                    f'--python_out={GRPC_OUT_DIR}',
                    f'--grpc_python_out={GRPC_OUT_DIR}',
                    proto_file
                ]
                print(f"生成 {proto_file} 的gRPC代码...")
                subprocess.run(cmd, check=True)
    
    # 修正导入路径问题，将生成的代码中的导入路径调整为相对路径
    fix_grpc_imports()
    
    print("gRPC代码生成完成!")

def fix_grpc_imports():
    """修复生成的gRPC代码中的导入路径问题"""
    for root, _, files in os.walk(GRPC_OUT_DIR):
        for file in files:
            if file.endswith('_pb2.py') or file.endswith('_pb2_grpc.py'):
                file_path = os.path.join(root, file)
                # 读取文件内容
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # 替换导入路径
                # 例如: from auth import CurrentUser_pb2 -> from core.grpc.auth import CurrentUser_pb2
                if 'from auth import' in content:
                    content = content.replace('from auth import', 'from core.grpc.auth import')
                
                # 写回文件
                with open(file_path, 'w') as f:
                    f.write(content)
                print(f"修复了 {file_path} 中的导入路径")

if __name__ == "__main__":
    generate_grpc_code()
