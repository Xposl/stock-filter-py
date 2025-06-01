# InvestNote API 模块架构

本目录包含 InvestNote-py 项目的 FastAPI 应用程序和 API 路由定义。

## 目录结构

```
api/
├── api.py                   # 主应用程序，包含基础路由和中间件
├── models.py                # 共享的 Pydantic 模型定义
├── routers/                 # 路由模块目录
│   ├── __init__.py          # 路由模块初始化文件
│   ├── ticker.py            # 股票 Ticker 相关路由
│   ├── news.py              # 新闻相关路由
│   └── scheduler.py         # 定时任务和调度器路由
└── README.md                # 本文档
```

## 模块拆分说明

### 🏗️ 重构概述

原本的 `api.py` 文件包含了所有 API 路由，代码行数超过 600 行，维护困难。现已按功能模块拆分为：

1. **主应用程序** (`api.py`) - 基础路由和中间件
2. **股票模块** (`routers/ticker.py`) - 股票数据相关功能
3. **新闻模块** (`routers/news.py`) - 新闻聚合和查询功能
4. **调度器模块** (`routers/scheduler.py`) - 定时任务和调度器管理

### 📦 主应用程序 (`api.py`)

**功能**: 应用程序入口、基础路由、中间件
**路由**:
- `GET /` - 根路径，返回服务信息
- `GET /me` - 获取当前认证用户信息

**特性**:
- FastAPI 应用实例创建和配置
- 全局异常处理中间件
- 路由模块注册和管理
- 认证中间件集成

### 📈 股票模块 (`routers/ticker.py`)

**功能**: 股票数据查询、列表分页、批量更新
**路由**:
- `POST /pages` - 获取股票列表（分页、搜索、排序）
- `GET /ticker/{market}/{ticker_code}` - 获取指定股票详细信息和K线数据
- `POST /cron/ticker/{market}/update` - 批量更新指定市场的股票评分

**特性**:
- 支持多市场：A股(zh)、港股(hk)、美股(us)
- 分页查询和动态排序
- 后台批量更新任务
- 集成 DataSourceHelper 数据源

### 📰 新闻模块 (`routers/news.py`)

**功能**: 新闻文章查询、新闻源管理
**路由**:
- `GET /news` - 获取新闻文章列表（分页、搜索、筛选）
- `GET /news/sources` - 获取新闻源列表
- `GET /news/{article_id}` - 获取单篇新闻文章详细信息

**特性**:
- 支持多维度筛选：时间范围、新闻源、状态
- 文章内容智能截断
- Repository 模式数据访问
- 异步数据库操作

### ⏰ 调度器模块 (`routers/scheduler.py`)

**功能**: 定时任务管理、新闻抓取调度
**路由**:
- `POST /cron/news` - 定时新闻抓取任务
- `GET /cron/news/status` - 获取新闻抓取状态和统计信息
- `GET /cron/news/scheduler` - 获取调度器状态和任务列表
- `POST /cron/news/scheduler/start` - 启动新闻调度器
- `POST /cron/news/scheduler/stop` - 停止新闻调度器
- `POST /cron/news/manual` - 手动触发新闻抓取

**特性**:
- 后台任务执行
- 调度器状态管理
- 新闻聚合统计
- 手动和自动抓取支持

## 🔧 技术架构

### 路由注册

```python
# api.py
from .routers import ticker, news, scheduler

app = FastAPI(...)

# 注册路由模块
app.include_router(ticker.router)
app.include_router(news.router)
app.include_router(scheduler.router)
```

### 路由器配置

每个路由模块都使用 FastAPI 的 `APIRouter` 来组织路由：

```python
# 示例：ticker.py
from fastapi import APIRouter

router = APIRouter(tags=["股票"])

@router.post("/pages")
async def get_ticker_pages(...):
    ...
```

### 依赖注入

所有模块共享以下依赖：
- `core.auth.auth_middleware.auth_required` - 认证中间件
- `core.data_source_helper.DataSourceHelper` - 数据源助手
- Repository 模式的数据访问层

### 错误处理

- 全局异常中间件记录API调用日志
- 各模块内部处理业务逻辑异常
- 统一的HTTP状态码和错误响应格式

## 🚀 使用指南

### 启动应用

```bash
# 开发模式
python main.py --reload

# 生产模式
python main.py --host 0.0.0.0 --port 8000
```

### API 文档

启动应用后访问：
- Swagger UI: `http://localhost:8000/investnote/docs`
- ReDoc: `http://localhost:8000/investnote/redoc`

### 添加新路由

1. 在对应的路由模块中添加新的路由函数
2. 如果需要新的功能模块，创建新的路由文件
3. 在 `api.py` 中注册新的路由模块

### 测试

```bash
# 运行API测试
pytest tests/integration/api/

# 启动测试服务器
python run_tests.py --type api
```

## 📋 迁移说明

### 从旧版本迁移

如果你正在从旧的单文件 `api.py` 迁移：

1. **路由路径保持不变** - 所有现有的API端点路径都保持原样
2. **导入路径调整** - 如果有其他模块直接导入API函数，需要更新导入路径
3. **测试更新** - 更新测试文件中的导入路径

### 向后兼容性

- ✅ 所有API端点路径保持不变
- ✅ 请求/响应格式保持不变
- ✅ 认证机制保持不变
- ✅ 中间件功能保持不变

## 🔄 持续集成

模块拆分后的优势：

1. **代码组织** - 按功能分组，便于维护
2. **并行开发** - 不同团队可以同时开发不同模块
3. **测试隔离** - 每个模块可以独立测试
4. **代码复用** - 共享的逻辑可以提取到公共模块

## 📚 相关文档

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [项目架构规范](.cursor/rules/fast-api/project_structure.mdc)
- [API 测试指南](../tests/README.md)
- [开发环境设置](../README.md) 