
import importlib
import pytest

def check_optional_dependency(module_name: str, skip_reason: str = None):
    """检查可选依赖是否可用"""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        if skip_reason:
            pytest.skip(skip_reason)
        return False

# AKShare 可用性检查
AKSHARE_AVAILABLE = check_optional_dependency("akshare")

# 网络服务可用性检查
def check_network_service(url: str, timeout: int = 5):
    """检查网络服务是否可用"""
    try:
        import requests
        response = requests.head(url, timeout=timeout)
        return response.status_code < 400
    except Exception:
        return False
