# InvestNote-py 技术上下文 (基于实际代码结构)

## 技术栈概览

### 核心框架与服务
- **FastAPI**: 现代、高性能的Python Web框架，用于构建API服务
- **Uvicorn**: ASGI服务器，用于运行FastAPI应用
- **SQLAlchemy**: Python SQL工具包和ORM，用于数据库交互
- **Pydantic**: 数据验证和设置管理库，确保数据一致性
- **aiohttp**: 异步HTTP客户端，用于新闻数据抓取

### AI与自然语言处理 (NLP) - 新增
- **OpenAI API**: GPT系列模型集成，用于新闻分析和洞察提取
- **LangChain**: Agent框架，构建和管理多个协同工作的AI Agent
- **spaCy**: NLP基础库，用于实体识别、分词、词性标注
- **NLTK**: 自然语言处理工具包，文本分析和语料处理
- **Sentence Transformers**: 文本向量化，用于语义相似度计算
- **FAISS**: 向量相似度搜索，高效检索相关新闻和投资主题
- **ChromaDB**: 向量数据库，存储和管理文本嵌入

### 数据处理与分析
- **Pandas**: 数据分析和操作库，处理表格化数据
- **NumPy**: 数值计算库，支持大规模数组和矩阵运算
- **Matplotlib**: 数据可视化库，生成图表和分析报告

### 数据源与新闻聚合 - 新增
- **feedparser**: RSS源解析，从新闻网站获取结构化内容
- **newspaper3k**: 新闻内容提取，从网页提取正文和元数据
- **beautifulsoup4**: HTML解析，网页内容抓取
- **readability**: 网页可读性优化，提取核心内容
- **httpx**: HTTP客户端，高性能网络请求

### 股票市场数据接口 (现有)
- **AKShare**: 中国股票市场数据获取
- **Futu API**: 港股、美股实时数据接口
- **现有数据源辅助类**: `DataSourceHelper` 统一管理多市场数据

### 消息队列与任务调度 - 新增
- **Celery**: 分布式任务队列，异步处理新闻抓取和AI分析
- **Redis**: 消息代理和缓存，支持Celery任务队列

### 数据存储
- **PostgreSQL**: 主要关系型数据库 (生产环境)
- **SQLite**: 开发环境数据库
- **Redis**: 缓存层，提升API响应性能

### 认证与安全 (现有)
- **gRPC**: 微服务间通信，认证服务集成
- **JWT**: token认证，用户会话管理
- **python-jose**: JWT token处理

### 测试与质量保证
- **pytest**: 测试框架
- **pytest-asyncio**: 异步测试支持

### 部署与容器化
- **Docker**: 容器化部署
- **docker-compose**: 本地多容器编排

## 实际项目架构 (基于代码扫描)

### 三层架构模式
```
API层 (api/) → Handler层 (core/handler/) → Repository层 (core/service/) → Model层 (core/models/)
```

### 详细模块结构
```
InvestNote-py/
├── main.py                          # FastAPI应用启动入口
├── api/                            # API接口层
│   ├── api.py                      # 路由定义和请求处理
│   └── models.py                   # API请求/响应模型
├── core/                           # 核心业务逻辑层
│   ├── models/                     # 数据模型层 (SQLAlchemy ORM)
│   │   ├── ticker*.py              # 股票相关模型 (已实现)
│   │   ├── news_source.py          # 新闻源配置模型 (新增)
│   │   ├── news_article.py         # 新闻文章模型 (新增)
│   │   └── api_log.py              # API访问日志模型
│   ├── service/                    # 数据访问层 (Repository模式)
│   │   ├── ticker_repository.py    # 股票数据仓储 (已实现)
│   │   ├── ticker_*_repository.py  # 各类股票指标仓储 (已实现)
│   │   └── api_log_repository.py   # 日志仓储 (已实现)
│   ├── handler/                    # 业务处理层
│   │   ├── ticker_*_handler.py     # 股票分析处理器 (已实现)
│   │   └── ticker_filter_handler.py
│   ├── news_aggregator/            # 新闻聚合模块 (新增)
│   │   ├── rss_aggregator.py       # RSS新闻聚合器 (已实现)
│   │   └── news_aggregator_manager.py # 聚合管理器 (待实现)
│   ├── ai_agents/                  # AI代理模块 (框架就绪)
│   │   └── base_agent.py           # 代理基类 (待实现)
│   ├── nlp_utils/                  # NLP工具模块 (框架就绪)
│   ├── opportunity_detector/       # 投资机会检测 (框架就绪)
│   ├── quantitative_analyzer/      # 量化分析模块 (框架就绪)
│   ├── database/                   # 数据库工具
│   │   └── news_db_init.py         # 新闻DB初始化 (已实现)
│   ├── auth/                       # 认证模块 (已实现)
│   │   ├── auth_middleware.py      # 认证中间件
│   │   └── auth_grpc_client.py     # gRPC认证客户端
│   ├── analysis/                   # 股票分析模块 (已实现)
│   ├── strategy/                   # 投资策略模块 (已实现)
│   ├── indicator/                  # 技术指标模块 (已实现)
│   ├── valuation/                  # 估值模块 (已实现)
│   ├── score/                      # 评分模块 (已实现)
│   ├── filter/                     # 筛选模块 (已实现)
│   ├── utils/                      # 工具函数
│   └── data_source_helper.py       # 数据源管理 (已实现)
├── workers/                        # 异步任务模块 (框架就绪)
├── config/                         # 配置文件目录
├── proto/                          # gRPC协议定义
├── tools/                          # 开发工具
│   └── generate_grpc_code.py       # gRPC代码生成
├── test/                           # 测试目录
├── sql/                            # SQL脚本
├── memory-bank/                    # Memory Bank系统
└── invest_note.py                  # CLI工具 (已实现)
```

### 实际数据流程 (当前状态)

#### 现有功能 (已实现)
1. **股票数据管理**: `DataSourceHelper` → 多市场数据接口 → 数据库存储
2. **用户认证**: gRPC认证服务 → JWT Token → API访问控制  
3. **股票分析**: Handler层业务逻辑 → Repository层数据访问 → 评分/策略/估值计算
4. **API服务**: FastAPI路由 → 分页查询 → 股票列表/详情返回

#### 新增功能 (部分实现)
1. **新闻聚合**: RSS源配置 → 定时抓取 → 内容解析 → 数据库存储
2. **数据库扩展**: 新闻源表 + 新闻文章表 + 初始化脚本

#### 待实现功能 (框架就绪)
1. **AI多代理分析**: 新闻内容 → 多Agent并行分析 → 投资洞察提取
2. **机会检测**: 新闻分析结果 → 股票关联 → 投资机会识别
3. **量化验证**: 机会候选 → 资金流分析 → 市场热度验证
4. **异步任务**: Celery任务队列 → 后台处理 → 结果推送

## 数据库设计 (实际表结构)

### 现有数据表 (已实现)
- **ticker**: 股票基础信息
- **ticker_score**: 股票评分数据
- **ticker_strategy**: 投资策略数据  
- **ticker_valuation**: 估值数据
- **ticker_indicator**: 技术指标数据
- **api_log**: API访问日志

### 新增数据表 (已设计)
- **news_sources**: 新闻源配置表
  - 支持RSS、API、网站等多种源类型
  - 包含抓取频率、过滤规则、状态管理
- **news_articles**: 新闻文章表
  - 存储原文、摘要、NLP处理结果
  - 支持重要性评分、市场相关性评分
  - 包含实体识别、关键词、主题分析结果

### 待设计数据表
- **agent_analysis_results**: AI代理分析结果
- **investment_opportunities**: 投资机会记录
- **stock_news_correlations**: 股票-新闻关联关系
- **vector_embeddings**: 文本向量嵌入 (或使用向量数据库)

## 核心技术实现细节

### 1. 三层架构实现
```python
# API层 - 处理HTTP请求
@app.get("/ticker/{market}/{ticker_code}")
async def get_ticker_data(market: str, ticker_code: str):
    handler = TickerHandler()
    return await handler.get_ticker_analysis(market, ticker_code)

# Handler层 - 业务逻辑协调
class TickerHandler:
    def __init__(self):
        self.ticker_repo = TickerRepository()
        self.score_repo = TickerScoreRepository()
    
    async def get_ticker_analysis(self, market: str, code: str):
        # 协调多个Repository，执行业务逻辑
        pass

# Repository层 - 数据访问
class TickerRepository:
    async def get_by_code(self, code: str):
        # 封装具体的数据库查询逻辑
        pass
```

### 2. 新闻聚合实现
```python
class RSSAggregator:
    async def fetch_rss_feed(self, news_source: NewsSource):
        # 异步抓取RSS内容
        # 解析文章数据
        # 过滤和去重
        # 返回结构化数据
        pass
```

### 3. 认证集成 (已实现)
- gRPC客户端连接认证服务
- 中间件实现token验证
- 基于角色的访问控制

## 性能与可扩展性考虑

### 当前性能特点
- **异步I/O**: 全面使用async/await处理数据库和网络操作
- **连接池**: 数据库连接复用，减少连接开销
- **分页查询**: API支持分页，避免大数据量查询
- **索引优化**: 数据库表使用适当索引提升查询性能

### 扩展性设计
- **模块化架构**: 新功能可独立开发和部署
- **异步任务**: Celery支持水平扩展处理能力
- **缓存策略**: Redis缓存热点数据
- **微服务就绪**: gRPC接口支持服务拆分

### 待优化项目
- **向量数据库集成**: 支持大规模语义搜索
- **批处理优化**: 新闻处理的批量操作
- **实时推送**: WebSocket或SSE实现实时数据推送
- **监控告警**: 系统健康监控和性能指标收集

## 部署架构

### 开发环境
- SQLite数据库
- 本地Redis实例
- 单进程FastAPI应用

### 生产环境 (设计)
- PostgreSQL主从架构
- Redis集群
- Nginx负载均衡
- Docker容器化部署
- Kubernetes编排 (可选)

## 安全考虑

### 已实现安全特性
- JWT token认证
- gRPC安全通信
- SQL注入防护 (SQLAlchemy ORM)
- 输入验证 (Pydantic)

### 待加强安全特性
- API密钥安全管理
- LLM交互安全控制
- 敏感数据加密存储
- 访问日志审计 