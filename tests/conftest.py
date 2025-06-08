#!/usr/bin/env python3

"""
Pytest 共享 fixtures 和配置
为所有测试提供通用的设置和依赖项
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置测试环境变量
os.environ["DATABASE_TYPE"] = "sqlite"
os.environ["DATABASE_PATH"] = ":memory:"
os.environ["AUTH_ENABLED"] = "false"
os.environ["LOG_LEVEL"] = "WARNING"  # 减少测试时的日志输出

# 导入应用
from api.api import app  # noqa: E402
from core.database.db_adapter import DbAdapter  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """自动设置测试环境"""
    # 设置测试环境变量
    os.environ["TESTING"] = "true"
    yield
    # 测试结束后清理
    if "TESTING" in os.environ:
        del os.environ["TESTING"]


@pytest.fixture(scope="function")
def test_client():
    """
    FastAPI TestClient fixture
    为每个测试函数提供独立的客户端实例
    """
    client = TestClient(app)
    return client


@pytest.fixture(scope="function")
def mock_db_adapter():
    """
    模拟数据库适配器
    用于单元测试，避免实际数据库操作
    """
    mock_db = Mock(spec=DbAdapter)
    mock_db.query.return_value = []
    mock_db.query_one.return_value = None
    mock_db.execute.return_value = None
    mock_db.commit.return_value = None
    mock_db.rollback.return_value = None
    return mock_db


@pytest.fixture(scope="session")
def test_database():
    """
    测试数据库session fixture
    为集成测试提供独立的数据库实例
    """
    # 使用内存SQLite数据库进行测试
    db = DbAdapter()
    yield db
    # 测试结束后清理
    db.close() if hasattr(db, 'close') else None


@pytest.fixture(scope="function")
def clean_database(test_database):
    """
    每个测试函数都使用干净的数据库
    在测试前后清理数据
    """
    # 测试前清理（如果需要）
    yield test_database
    # 测试后清理（如果需要）


# pytest配置
def pytest_configure(config):
    """pytest配置钩子"""
    # 配置测试标记
    config.addinivalue_line(
        "markers", "unit: 标记单元测试"
    )
    config.addinivalue_line(
        "markers", "integration: 标记集成测试"
    )
    config.addinivalue_line(
        "markers", "slow: 标记慢速测试"
    )
    config.addinivalue_line(
        "markers", "api: 标记API测试"
    )
    config.addinivalue_line(
        "markers", "database: 标记数据库测试"
    )
    config.addinivalue_line(
        "markers", "debug: 标记调试测试"
    )
    config.addinivalue_line(
        "markers", "pocketflow: 标记PocketFlow AI测试"
    )
    config.addinivalue_line(
        "markers", "akshare: 标记AKShare数据源测试"
    )
    config.addinivalue_line(
        "markers", "xueqiu: 标记雪球数据源测试"
    )
    config.addinivalue_line(
        "markers", "news: 标记新闻聚合测试"
    )


# pytest命令行选项
def pytest_addoption(parser):
    """添加自定义命令行选项"""
    parser.addoption(
        "--run-slow", action="store_true", default=False,
        help="运行标记为slow的测试"
    )


def pytest_collection_modifyitems(config, items):
    """根据命令行选项修改测试收集"""
    if config.getoption("--run-slow"):
        # 如果指定运行slow测试，则跳过此配置
        return

    skip_slow = pytest.mark.skip(reason="需要 --run-slow 选项运行")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


# 异步测试配置
pytest_plugins = ["pytest_asyncio"]
