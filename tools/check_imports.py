import sys
import os

print("Python路径:")
for p in sys.path:
    print(f"  - {p}")

print("\n尝试导入模块:")
try:
    from core.auth.auth_grpc_client import auth_client
    print("✅ 导入 auth_client 成功")
except ImportError as e:
    print(f"❌ 导入 auth_client 失败: {e}")
    
    # 尝试动态添加路径
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"\n添加项目根路径 {project_root} 到 sys.path")
    sys.path.insert(0, project_root)
    
    try:
        from core.auth.auth_grpc_client import auth_client
        print("✅ 添加路径后导入 auth_client 成功")
    except ImportError as e2:
        print(f"❌ 添加路径后导入仍然失败: {e2}")
