# InvestNote-py 测试套件

本目录包含 InvestNote-py 项目的所有测试代码，按照 FastAPI 测试规范组织。

## 目录结构

```
tests/
├── conftest.py                          # Pytest 共享 fixtures 和配置
├── unit/                                # 单元测试
│   ├── test_models.py                   # 数据模型单元测试
│   └── test_repositories.py             # Repository 层单元测试
├── integration/                         # 集成测试
│   ├── api/                             # API 集成测试
│   │   └── test_news_api.py             # 新闻 API 集成测试
│   ├── services/                        # 服务层集成测试
│   │   ├── test_data_providers.py       # 数据提供者集成测试
│   │   └── test_news_aggregation.py     # 新闻聚合集成测试
│   └── database/                        # 数据库集成测试
└── debug/                               # 调试测试
    └── test_development_helpers.py      # 开发调试辅助测试
```

## 测试类型

### 单元测试 (Unit Tests)
- **目录**: `tests/unit/`
- **标记**: `@pytest.mark.unit`
- **特点**: 快速、独立、使用模拟对象
- **测试内容**: 单个函数、方法或类的功能

### 集成测试 (Integration Tests)
- **目录**: `tests/integration/`
- **标记**: `@pytest.mark.integration`
- **特点**: 测试组件间交互、可能较慢
- **子分类**:
  - **API 测试**: `@pytest.mark.api` - 测试 HTTP 端点
  - **数据库测试**: `@pytest.mark.database` - 测试数据库操作
  - **慢速测试**: `@pytest.mark.slow` - 涉及外部服务的测试

### 调试测试 (Debug Tests)
- **目录**: `tests/debug/`
- **标记**: `@pytest.mark.debug`
- **特点**: 开发调试用，不包含在正式测试套件中

## 运行测试

### 运行所有测试
```bash
pytest
```

### 运行特定类型的测试
```bash
# 仅运行单元测试
pytest -m unit

# 仅运行集成测试
pytest -m integration

# 仅运行 API 测试
pytest -m api

# 运行快速测试（排除慢速测试）
pytest -m "not slow"

# 运行包含慢速测试的完整测试
pytest --run-slow
```

### 运行特定文件的测试
```bash
# 运行新闻 API 测试
pytest tests/integration/api/test_news_api.py

# 运行数据模型单元测试
pytest tests/unit/test_models.py

# 运行调试测试
pytest tests/debug/ -m debug
```

### 运行特定测试函数
```bash
pytest tests/unit/test_models.py::TestNewsSourceModel::test_news_source_creation_valid
```

### 生成测试覆盖率报告
```bash
# 生成命令行覆盖率报告
pytest --cov=core --cov=api

# 生成 HTML 覆盖率报告
pytest --cov=core --cov=api --cov-report=html

# 查看 HTML 报告
open htmlcov/index.html
```

## 测试配置

### 环境变量
测试会自动设置以下环境变量：
- `DATABASE_TYPE=sqlite`
- `DATABASE_PATH=:memory:`
- `AUTH_ENABLED=false`
- `LOG_LEVEL=WARNING`
- `TESTING=true`

### Pytest 标记
- `unit`: 单元测试
- `integration`: 集成测试
- `api`: API 测试
- `database`: 数据库测试
- `slow`: 慢速测试
- `debug`: 调试测试

### Fixtures
- `test_client`: FastAPI TestClient 实例
- `mock_db_adapter`: 模拟数据库适配器
- `test_database`: 测试数据库实例
- `clean_database`: 每个测试的干净数据库

## 编写新测试

### 单元测试示例
```python
import pytest
from unittest.mock import Mock

@pytest.mark.unit
class TestYourComponent:
    """测试您的组件"""
    
    def test_your_function(self, mock_db_adapter):
        """测试您的函数"""
        # Arrange
        expected_result = "expected"
        
        # Act
        result = your_function()
        
        # Assert
        assert result == expected_result
```

### 集成测试示例
```python
import pytest

@pytest.mark.integration
@pytest.mark.api
class TestYourAPI:
    """测试您的API"""
    
    def test_your_endpoint(self, test_client):
        """测试您的端点"""
        # Act
        response = test_client.get("/your-endpoint")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
```

## 最佳实践

1. **遵循 AAA 模式**: Arrange (准备) → Act (执行) → Assert (断言)
2. **使用描述性的测试名称**: 清楚说明测试的内容和预期结果
3. **保持测试独立**: 每个测试应该独立运行，不依赖其他测试
4. **使用适当的标记**: 为测试添加正确的 pytest 标记
5. **模拟外部依赖**: 在单元测试中使用 mock 对象
6. **编写可维护的测试**: 测试代码也需要保持清洁和可维护

## 持续集成

在 CI/CD 流程中，可以分阶段运行测试：

1. **快速阶段**: 运行单元测试和快速集成测试
   ```bash
   pytest -m "unit or (integration and not slow)"
   ```

2. **完整阶段**: 运行所有测试包括慢速测试
   ```bash
   pytest --run-slow
   ```

## 故障排除

### 常见问题

1. **导入错误**: 确保项目根目录在 Python 路径中
2. **数据库错误**: 检查测试环境变量设置
3. **异步测试失败**: 确保安装了 `pytest-asyncio`
4. **模拟不工作**: 检查模拟对象的设置和使用

### 调试测试
```bash
# 详细输出
pytest -v

# 显示打印语句
pytest -s

# 调试模式
pytest --pdb

# 仅运行失败的测试
pytest --lf
```

## 相关文档

- [FastAPI 测试文档](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pytest 文档](https://docs.pytest.org/)
- [项目测试规范](.cursor/rules/fast-api/testing_guidelines.mdc) 