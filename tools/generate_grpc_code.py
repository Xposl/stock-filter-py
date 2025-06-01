#!/usr/bin/env python3
# filepath: /Users/xposl/Workspace/me/InvestNote-py/tools/generate_grpc_code.py
import os
import subprocess
import sys

# 项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# proto文件目录
PROTO_DIR = os.path.join(PROJECT_ROOT, "proto")
# 生成的grpc代码存放目录
GRPC_OUT_DIR = os.path.join(PROJECT_ROOT, "core/grpc")

def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def get_python_executable():
    """获取正确的 Python 可执行文件路径"""
    # 首先检查是否在虚拟环境中
    venv_path = os.path.join(PROJECT_ROOT, ".venv", "bin", "python")
    if os.path.exists(venv_path):
        return venv_path
    
    # 如果没有虚拟环境，使用当前的 Python
    return sys.executable

def check_grpc_tools():
    """检查 grpc_tools 是否可用"""
    python_exec = get_python_executable()
    try:
        result = subprocess.run(
            [python_exec, "-c", "import grpc_tools.protoc"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False

def install_grpc_tools():
    """安装 grpc_tools 如果不存在"""
    python_exec = get_python_executable()
    print("检测到 grpc_tools 未安装，正在安装...")
    try:
        subprocess.run([python_exec, "-m", "pip", "install", "grpcio", "grpcio-tools"], check=True)
        print("grpc_tools 安装成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"安装 grpc_tools 失败: {e}")
        return False

def generate_grpc_code():
    """生成gRPC代码"""
    # 检查并安装依赖
    if not check_grpc_tools():
        if not install_grpc_tools():
            print("错误: 无法安装必要的 grpc_tools 依赖")
            return False
    
    ensure_dir(GRPC_OUT_DIR)
    
    python_exec = get_python_executable()
    print(f"使用 Python: {python_exec}")
    
    # 遍历所有proto文件
    for root, _, files in os.walk(PROTO_DIR):
        for file in files:
            if file.endswith('.proto'):
                proto_file = os.path.join(root, file)
                # 对每个proto文件生成Python代码
                cmd = [
                    python_exec, '-m', 'grpc_tools.protoc',
                    f'--proto_path={PROTO_DIR}',
                    f'--python_out={GRPC_OUT_DIR}',
                    f'--grpc_python_out={GRPC_OUT_DIR}',
                    proto_file
                ]
                print(f"生成 {proto_file} 的gRPC代码...")
                try:
                    subprocess.run(cmd, check=True)
                except subprocess.CalledProcessError as e:
                    print(f"生成 {proto_file} 失败: {e}")
                    return False
    
    # 修正导入路径问题，将生成的代码中的导入路径调整为相对路径
    fix_grpc_imports()
    
    print("gRPC代码生成完成!")
    return True

def fix_grpc_imports():
    """修复生成的gRPC代码中的导入路径问题"""
    for root, _, files in os.walk(GRPC_OUT_DIR):
        for file in files:
            if file.endswith('_pb2.py') or file.endswith('_pb2_grpc.py'):
                file_path = os.path.join(root, file)
                try:
                    # 读取文件内容
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 替换导入路径
                    # 例如: from auth import CurrentUser_pb2 -> from core.grpc.auth import CurrentUser_pb2
                    if 'from auth import' in content:
                        content = content.replace('from auth import', 'from core.grpc.auth import')
                    
                    # 写回文件
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"修复了 {file_path} 中的导入路径")
                except Exception as e:
                    print(f"修复 {file_path} 导入路径时出错: {e}")

if __name__ == "__main__":
    try:
        success = generate_grpc_code()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"生成gRPC代码时发生错误: {e}")
        sys.exit(1)
