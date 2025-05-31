# InvestNote-py 技术上下文

## 技术栈概览

### 核心框架与服务
- **FastAPI**: 现代、高性能的Python Web框架，用于构建API服务。
- **Uvicorn**: ASGI服务器，用于运行FastAPI应用。
- **SQLAlchemy**: Python SQL工具包和ORM，用于数据库交互。
- **Pydantic**: 数据验证和设置管理库，确保数据一致性。

### AI与自然语言处理 (NLP)
- **大语言模型 (LLM) 集成**: 如 GPT API 或其他类似模型，用于深度文本理解、摘要、情感分析、因果推断等。
- **NLP基础库**: 如 `spaCy`, `NLTK`，用于实体识别、分词、词性标注等基础NLP任务。
- **Agent框架**: 可能采用 `LangChain` 或自研框架，用于构建和管理多个协同工作的AI Agent，每个Agent负责特定的分析任务（如行业影响、供应链关联等）。
- **文本向量化与相似度计算**: 如 `Sentence Transformers`, `FAISS`，用于新闻内容与投资主题的语义匹配。

### 数据处理与分析
- **Pandas**: 数据分析和操作库，处理表格化数据。
- **NumPy**: 数值计算库，支持大规模数组和矩阵运算。
- **SciPy**: 科学计算库，提供统计和优化工具。

### 数据源接口
- **全球新闻API**: 用于聚合来自不同源的实时新闻数据 (需调研和集成，如 NewsAPI, Bloomberg API, Reuters API等，或通过RSS聚合)。
- **股票市场数据API**: 如 `AKShare`, `Futu API`, `Polygon.io`, `IEX Cloud` 等，获取全球股票行情、财务数据。

### 消息队列与任务调度
- **Celery**: 分布式任务队列，用于异步处理耗时任务，如新闻抓取、AI分析、指标计算。
- **Redis/RabbitMQ**: 作为Celery的消息中间件，也可用于缓存。

### 数据存储
- **PostgreSQL**: 主要关系型数据库，存储结构化数据如用户信息、股票基本面数据、分析结果等。
- **SQLite**: 用于开发环境或轻量级本地存储。
- **向量数据库 (Vector Database)**: 如 `Pinecone`, `Weaviate`, `ChromaDB`，用于存储和高效检索新闻/文本的向量嵌入，支持语义搜索和相似性匹配。
- **缓存**: Redis，用于缓存常用数据、API响应、中间计算结果，提升性能。

### 量化与指标计算
- **TA-Lib** 或类似库: 用于计算技术分析指标。
- 自定义量化脚本: 实现特定的资金流分析、市场热度等指标。

### 测试与质量保证
- **pytest**: 测试框架。
- **pytest-asyncio**: 异步测试支持。

### 部署与容器化
- **Docker**: 容器化部署。
- **docker-compose**: 本地多容器编排。
- **Kubernetes (可选)**: 生产环境大规模部署和管理。

## 项目架构设计

### 模块结构 (调整后)
```
InvestNote-py/
├── main.py                 # FastAPI应用入口点
├── api/                    # API路由模块
├── core/                   # 核心业务逻辑
│   ├── news_aggregator/   # 新闻聚合与预处理模块
│   ├── ai_agents/         # AI Agent框架与具体Agent实现
│   │   ├── base_agent.py
│   │   ├── industry_analyzer_agent.py
│   │   └── supply_chain_agent.py
│   ├── nlp_utils/         # NLP工具函数和模型接口
│   ├── market_connector/  # 连接全球市场数据API
│   ├── quantitative_analyzer/ # 量化指标计算与资金流分析
│   ├── opportunity_detector/ # 投资机会发现与关联引擎
│   ├── models/            # 数据模型 (SQLAlchemy, Pydantic)
│   ├── services/          # 业务服务层
│   └── utils.py           # 通用工具函数
├── config/                # 配置文件
├── workers/               # Celery异步任务定义
├── proto/                 # gRPC协议文件 (如果仍用于内部服务)
├── tools/                 # 辅助工具
├── tests/                 # 测试文件
└── data/                  # 可能存放一些静态数据或本地数据源
```

### 数据流设计 (调整后)
1.  **新闻获取与预处理**: `news_aggregator`模块定时从配置的新闻源拉取数据，进行清洗、去重、NLP初步处理（如实体提取）。
2.  **异步任务分发**: 清洗后的新闻通过Celery分发给`ai_agents`进行分析。
3.  **多Agent协同分析**: 各Agent（如行业分析、地缘政治、供应链影响Agent）并行或串行处理新闻，输出结构化的分析见解和关联实体。
4.  **机会与关联发现**: `opportunity_detector`模块整合多Agent的分析结果，利用NLP和知识图谱技术（可选）构建影响链，匹配全球股票池，识别潜在投资主题和标的。
5.  **量化验证**: `quantitative_analyzer`模块对筛选出的股票进行资金流、市场热度等量化指标计算。
6.  **结果存储与推送**: 分析结果（新闻、AI洞察、关联股票、量化指标）存入数据库，并通过API模块触发向用户App推送。

### API设计模式
- **RESTful API**: FastAPI用于构建主要的面向用户的API。
- **异步处理**: 广泛使用`async/await`处理I/O密集型操作（新闻API调用、数据库操作等）。
- **事件驱动 (可选)**: 考虑使用事件总线（如Kafka或Redis Streams）在不同分析模块间传递消息，实现更松耦合的架构。

### AI Agent架构
- **可配置性**: Agent的行为、分析逻辑、调用的LLM模型等应可通过配置进行调整。
- **可扩展性**: 方便添加新的Agent类型以覆盖更多分析维度。
- **状态管理**: Agent执行过程中的状态（如中间分析结果）可能需要持久化或缓存。

## 数据库设计 (扩展)

### 新增或调整的数据模型
- **NewsArticle**: 存储聚合的新闻原文、元数据、NLP处理结果。
- **AgentAnalysisResult**: 存储每个Agent对新闻的分析结论和提取的关键信息。
- **InvestmentTheme**: 由AI分析出的潜在投资主题。
- **StockNewsCorrelation**: 新闻与股票之间的关联性、关联路径、置信度。
- **FundingFlowMetrics**: 股票的资金流相关量化指标历史。
- **VectorEmbeddings**: (如果使用向量数据库) 存储新闻文本或关键片段的向量嵌入。

## 外部依赖 (扩展)

- **新闻API服务**: 依赖其稳定性、覆盖范围、更新频率和API调用限制。
- **LLM API服务**: 依赖其可用性、成本、响应延迟和模型能力。
- **市场数据API**: 依赖其数据质量、实时性和API限制。

## 性能考虑 (扩展)

- **NLP处理效率**: 大量新闻文本的NLP处理可能成为瓶颈，考虑批处理、模型优化和硬件加速（如GPU）。
- **Agent分析并发**: 同时处理多条新闻或单个新闻的多个Agent分析，需要高效的并发管理和资源调度。
- **向量检索性能**: 如果使用向量数据库，其在高并发下的检索效率至关重要。
- **实时性要求**: 从新闻发生到机会推送到用户的端到端延迟是关键指标。

## 安全考虑 (扩展)
- **API密钥管理**: 安全存储和使用各类外部API的密钥。
- **LLM交互安全**: 防止Prompt注入等针对LLM的攻击，确保Agent分析的客观性和安全性。
- **数据隐私**: 如果用户可配置Agent或提供私有数据，需考虑数据隔离和隐私保护。 