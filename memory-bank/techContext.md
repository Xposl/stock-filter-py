# InvestNote-py 技术上下文 (2025.06.01 更新)

## 技术栈概览

### 核心框架与服务
- **FastAPI**: 现代、高性能的Python Web框架，用于构建API服务
- **Uvicorn**: ASGI服务器，用于运行FastAPI应用
- **SQLAlchemy**: Python SQL工具包和ORM，用于数据库交互
- **Pydantic**: 数据验证和设置管理库，确保数据一致性
- **aiohttp**: 异步HTTP客户端，用于新闻数据抓取

### 🆕 AI与自然语言处理 (基于PocketFlow)
- **PocketFlow**: 100行LLM工作流框架，专为AI Agent构建
  - GitHub: https://github.com/The-Pocket/PocketFlow (5.2k星)
  - 版本: v0.0.2，已成功集成
- **千问LLM**: 阿里云大语言模型服务，主要AI分析引擎
- **硅基流动API**: OpenAI兼容接口，作为千问的备用LLM服务
- **ChromaDB**: 嵌入式向量数据库，用于新闻语义相似性分析
- **Sentence Transformers**: 文本向量化，语义相似度计算
- **OpenAI**: GPT系列模型集成（备用方案）

### 股票数据源集成 (已完成)
- **AKShare**: 中国股票市场数据获取，最高优先级数据源
- **雪球API**: 股票数据和新闻聚合，补充数据源
- **数据提供者层**: 统一抽象接口，支持智能降级
- **多市场支持**: A股、港股、美股统一处理

### 新闻聚合与处理 (已实现)
- **feedparser**: RSS源解析，从新闻网站获取结构化内容
- **newspaper3k**: 新闻内容提取，从网页提取正文和元数据
- **beautifulsoup4**: HTML解析，网页内容抓取
- **readability**: 网页可读性优化，提取核心内容
- **lxml_html_clean**: HTML内容清理和安全处理

### 消息队列与任务调度
- **Celery**: 分布式任务队列，异步处理新闻抓取和AI分析
- **Redis**: 消息代理和缓存，支持Celery任务队列
- **APScheduler**: 定时任务调度器

### 数据存储
- **MySQL**: 主要关系型数据库 (生产环境)
- **PostgreSQL**: 企业级数据库选项
- **SQLite**: 开发环境数据库
- **ChromaDB**: 向量数据库，嵌入式部署

### 认证与安全 (已实现)
- **gRPC**: 微服务间通信，认证服务集成
- **JWT**: token认证，用户会话管理
- **python-jose**: JWT token处理

### 测试与质量保证
- **pytest**: 测试框架
- **pytest-asyncio**: 异步测试支持
- **pytest-cov**: 测试覆盖率统计

### 部署与容器化
- **Docker**: 容器化部署
- **docker-compose**: 本地多容器编排

## 实际项目架构 (基于当前代码库)

### 三层架构模式 + AI分析层
```
API层 (api/) → Handler层 (core/handler/) → Repository层 (core/service/) → Model层 (core/models/)
                     ↓
               AI分析层 (core/ai_agents/) → PocketFlow工作流 → 千问LLM
```

### 详细模块结构 (当前状态)
```
InvestNote-py/
├── main.py                          # FastAPI应用启动入口
├── api/                            # API接口层
│   ├── api.py                      # 主路由配置 ✅
│   ├── models.py                   # API请求/响应模型 ✅
│   └── routers/                    # 路由模块化 ✅
│       ├── ticker.py               # 股票相关路由
│       ├── news.py                 # 新闻相关路由
│       └── scheduler.py            # 定时任务路由
├── core/                           # 核心业务逻辑层
│   ├── models/                     # 数据模型层 (Pydantic) ✅
│   │   ├── ticker*.py              # 股票相关模型
│   │   ├── news_source.py          # 新闻源配置模型 ✅
│   │   ├── news_article.py         # 新闻文章模型 ✅
│   │   └── api_log.py              # API访问日志模型
│   ├── service/                    # 数据访问层 (Repository) ✅
│   │   ├── ticker_repository.py    # 股票数据仓储
│   │   ├── ticker_*_repository.py  # 各类股票指标仓储
│   │   └── news_*_repository.py    # 新闻相关仓储
│   ├── handler/                    # 业务处理层 ✅
│   │   ├── ticker_*_handler.py     # 股票分析处理器
│   │   └── news_*_handler.py       # 新闻处理器
│   ├── data_providers/             # 数据提供者层 ✅
│   │   ├── stock_data_provider.py  # 统一股票数据接口
│   │   ├── akshare_provider.py     # AKShare数据提供者
│   │   ├── xueqiu_provider.py      # 雪球数据提供者
│   │   └── stock_data_factory.py   # 策略工厂模式
│   ├── utils/                      # 工具层 ✅
│   │   └── xueqiu/                 # 雪球抽象层
│   │       ├── xueqiu_base_client.py
│   │       ├── xueqiu_news_client.py
│   │       ├── xueqiu_stock_client.py
│   │       └── xueqiu_client_factory.py
│   ├── news_aggregator/            # 新闻聚合模块 ✅
│   │   ├── rss_aggregator.py       # RSS新闻聚合器
│   │   ├── xueqiu_aggregator.py    # 雪球新闻聚合器
│   │   └── news_aggregator_manager.py # 聚合管理器
│   ├── ai_agents/                  # AI代理模块 🆕
│   │   ├── flow_definitions/       # PocketFlow工作流定义
│   │   ├── llm_clients/           # LLM客户端 (千问、硅基流动)
│   │   ├── vector_store/          # ChromaDB向量存储
│   │   ├── analyzers/             # 分析器组件
│   │   └── utils/                 # AI工具类
│   ├── nlp_utils/                  # NLP工具模块 ✅
│   ├── database/                   # 数据库工具 ✅
│   │   ├── db_adapter.py           # 数据库适配器
│   │   └── news_db_init.py         # 新闻DB初始化
│   ├── auth/                       # 认证模块 ✅
│   │   ├── auth_middleware.py      # 认证中间件
│   │   └── auth_grpc_client.py     # gRPC认证客户端
│   ├── analysis/                   # 股票分析模块 ✅
│   ├── strategy/                   # 投资策略模块 ✅
│   ├── indicator/                  # 技术指标模块 ✅
│   ├── valuation/                  # 估值模块 ✅
│   ├── score/                      # 评分模块 ✅
│   ├── filter/                     # 筛选模块 ✅
│   ├── scheduler/                  # 调度器模块 ✅
│   ├── grpc/                       # gRPC模块 ✅
│   ├── enum/                       # 枚举定义 ✅
│   ├── schema/                     # 数据Schema ✅
│   └── data_source_helper.py       # 数据源管理 ✅
├── scripts/                        # 开发脚本 ✅
├── tests/                          # 测试目录 ✅
├── sql/                            # SQL脚本 ✅
├── proto/                          # gRPC协议定义 ✅
├── memory-bank/                    # Memory Bank系统 ✅
├── docs/                           # 文档目录 ✅
└── invest_note.py                  # CLI工具 ✅
```

### 🆕 AI分析流水线架构
```
新闻输入 → PocketFlow工作流引擎
    ↓
规则预筛选层 (关键词过滤、来源权重、时效性)
    ↓
AI深度分析层 (千问LLM调用、Token优化)
    ↓
情感评估层 (情感打分、市场影响度、风险评估)
    ↓
投资建议层 (股票关联计算、短期投资评估、风险等级)
    ↓
向量相似性层 (ChromaDB检索、语义相似性、历史对比)
```

## 数据库设计 (当前状态)

### 已实现数据表
- **ticker**: 股票基础信息 ✅
- **ticker_score**: 股票评分数据 ✅
- **ticker_strategy**: 投资策略数据 ✅
- **ticker_valuation**: 估值数据 ✅
- **ticker_indicator**: 技术指标数据 ✅
- **api_log**: API访问日志 ✅
- **news_sources**: 新闻源配置表 ✅
- **news_articles**: 新闻文章表 (包含AI分析字段) ✅

### 待扩展字段 (AI分析相关)
- **news_articles.ai_analysis_result**: JSON字段存储AI分析结果
- **news_articles.sentiment_score**: 情感分析评分
- **news_articles.investment_advice**: 投资建议内容
- **news_articles.stock_correlations**: 股票关联度数据

## 核心技术实现模式

### 1. 数据提供者模式 (已实现)
```python
# 统一的股票数据访问接口
from core.data_providers.stock_data_factory import get_stock_quote

# 自动选择最佳数据源 (AKShare优先，雪球补充)
response = get_stock_quote("600000", market=StockMarket.A_SHARE)
```

### 2. 雪球抽象层 (已实现)
```python
# 统一的雪球客户端访问
from core.utils.xueqiu.xueqiu_client_factory import create_stock_client

async with create_stock_client() as client:
    quote = await client.get_stock_quote_async("SH600000")
```

### 3. PocketFlow AI工作流 (新实现)
```python
# 基于PocketFlow的新闻分析工作流
from core.ai_agents import NewsAnalysisFlow

flow = NewsAnalysisFlow()
result = await flow.run({
    "articles": pending_articles,
    "analysis_type": "batch"
})
```

### 4. 新闻聚合模式 (已实现)
```python
# RSS和API统一聚合管理
from core.news_aggregator import NewsAggregatorManager

manager = NewsAggregatorManager()
articles = await manager.aggregate_all_sources()
```

## 当前技术状态总结

### ✅ 已完成模块
- FastAPI基础架构和路由系统
- 三层架构（API-Handler-Repository-Model）
- 股票数据多源集成（AKShare + 雪球）
- 新闻聚合系统（RSS + API）
- 数据库设计和初始化
- 认证和安全机制
- Docker容器化部署

### 🔄 进行中模块
- **PocketFlow AI分析系统** (30%完成)
  - 框架已集成，目录结构已创建
  - 千问LLM客户端待实现
  - ChromaDB向量存储待配置
  - 工作流定义待开发

### ⏳ 待开始模块
- Multi-Agent协作系统
- MCP协议集成
- 高级投资策略分析
- 实时监控和告警

### 🎯 技术重点 (2025.06.01)
1. **AI分析模块实现**: 基于PocketFlow的新闻分析工作流
2. **Token优化策略**: 千问API成本控制和性能优化
3. **向量相似性**: ChromaDB嵌入式部署和语义分析
4. **系统集成**: AI分析结果与现有Handler层无缝集成 