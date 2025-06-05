# InvestNote-py 技术上下文

## 核心技术栈 (当前实现)

### 🏗️ Web框架与服务
- **FastAPI**: 现代、高性能的Python Web框架，API服务核心
- **Uvicorn**: ASGI服务器，支持高并发异步处理
- **Pydantic**: 数据验证和类型安全，所有模型基于BaseModel
- **aiohttp**: 异步HTTP客户端，外部API调用

### 🤖 AI与机器学习引擎 (已集成)
- **PocketFlow**: 100行LLM工作流框架，AI分析流水线核心
  - GitHub: https://github.com/The-Pocket/PocketFlow
  - 轻量级设计，专为复杂AI工作流构建
- **千问LLM**: 阿里云大语言模型，主要AI分析引擎
- **硅基流动API**: OpenAI兼容接口，千问的备用LLM服务
- **ChromaDB**: 嵌入式向量数据库，语义相似性分析
- **Sentence Transformers**: 文本向量化和语义相似度计算

### 📊 股票数据源架构 (已完成)
- **AKShare**: 优先级100，主要股票数据源
  - 支持A股、港股、美股完整数据
  - 实时行情、历史数据、公司信息、股票搜索
- **雪球API**: 优先级50，补充数据源
  - 基于重构后的抽象层实现
  - 统一的客户端工厂和会话管理
- **数据提供者工厂**: 策略模式智能降级
  - 错误计数和可用性监控
  - 自动切换和恢复机制

### 📰 新闻聚合技术栈 (已实现)
- **feedparser**: RSS源解析和内容提取
- **newspaper3k**: 新闻网页内容提取和元数据解析
- **beautifulsoup4**: HTML解析和内容抓取
- **readability**: 网页可读性优化和核心内容提取
- **lxml_html_clean**: HTML内容清理和安全处理

### 🗄️ 数据存储层
- **MySQL**: 生产环境主数据库，完整关系型数据支持
- **SQLite**: 开发环境数据库，轻量级快速开发
- **ChromaDB**: 向量数据库，嵌入式部署，支持语义检索
- **DbAdapter**: 统一数据库适配器，支持多数据库类型自动转换

### 🔒 认证与安全 (已实现)
- **gRPC**: 微服务间通信，认证服务集成
- **JWT Token**: 用户会话管理和API认证
- **python-jose**: JWT token处理和验证
- **认证中间件**: FastAPI中间件实现统一认证

### 🧪 测试与质量保证
- **pytest**: 主要测试框架
- **pytest-asyncio**: 异步代码测试支持
- **pytest-cov**: 测试覆盖率统计
- **类型检查**: Python类型提示 + mypy支持

### 🚀 部署与容器化
- **Docker**: 容器化部署支持
- **docker-compose**: 多容器编排和环境管理
- **自动化部署脚本**: deploy.sh支持版本管理和crontab同步

## 项目架构详解 (当前状态)

### 三层业务架构
```
┌─────────────────────────────────────────────────────────────┐
│                    API层 (api/)                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │   ticker    │ │    news     │ │      scheduler         │ │
│  │   routes    │ │   routes    │ │      routes            │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────┐
│                Handler层 (core/handler/)                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │   ticker    │ │    news     │ │    AI analysis         │ │
│  │  analysis   │ │  handler    │ │     handler            │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────┐
│              Repository层 (core/service/)                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │   ticker    │ │    news     │ │      score             │ │
│  │ repository  │ │ repository  │ │   repository           │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────┐
│               Model层 (core/models/)                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │   Ticker    │ │ NewsArticle │ │    TickerScore         │ │
│  │  (Pydantic) │ │ (Pydantic)  │ │    (Pydantic)          │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 数据提供者层架构 (已实现)
```
┌─────────────────────────────────────────────────────────────┐
│                StockDataFactory (策略工厂)                  │
│              ┌─────────────────────────────────┐            │
│              │    智能数据源选择和降级策略       │            │
│              └─────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌──────────────────┐ ┌──────────────────┐ ┌─────────────────┐
│  AKShareProvider │ │  XueqiuProvider  │ │  FutureProvider │
│   (优先级: 100)   │ │   (优先级: 50)   │ │   (预留扩展)     │
│                  │ │                  │ │                 │
│ • A股、港股、美股 │ │ • 补充数据源     │ │ • 期货、期权     │
│ • 实时行情数据   │ │ • 新闻时间线     │ │ • 衍生品数据     │
│ • 历史K线数据    │ │ • 社区情绪数据   │ │                 │
│ • 公司基本信息   │ │                  │ │                 │
│ • 股票搜索功能   │ │                  │ │                 │
└──────────────────┘ └──────────────────┘ └─────────────────┘
```

### 雪球抽象层架构 (已重构)
```
┌─────────────────────────────────────────────────────────────┐
│              XueqiuClientFactory (客户端工厂)               │
│              ┌─────────────────────────────────┐            │
│              │      统一配置和会话管理          │            │
│              └─────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌──────────────────┐ ┌──────────────────┐ ┌─────────────────┐
│XueqiuBaseClient  │ │XueqiuNewsClient  │ │XueqiuStockClient│
│                  │ │                  │ │                 │
│ • 会话管理       │ │ • 新闻时间线     │ │ • 股票行情       │
│ • 令牌获取       │ │ • 股票新闻       │ │ • 公司信息       │
│ • HTTP请求封装   │ │ • 重要性评分     │ │ • 多市场支持     │
│ • 错误处理       │ │ • 内容过滤       │ │ • 实时数据       │
│ • 重试机制       │ │                  │ │                 │
└──────────────────┘ └──────────────────┘ └─────────────────┘
```

### AI分析流水线 (基于PocketFlow)
```
┌─────────────────────────────────────────────────────────────┐
│                    新闻输入 (RSS/API)                       │
└─────────────────────────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────┐
│               规则预筛选层 (Rule-based Filter)              │
│  • 关键词过滤  • 来源权重  • 时效性检查  • 重复检测         │
└─────────────────────────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────┐
│              AI深度分析层 (PocketFlow + 千问LLM)             │
│  • 事件识别  • 影响链分析  • 行业关联  • Token优化           │
└─────────────────────────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────┐
│               情感评估层 (Sentiment Analysis)               │
│  • 情感打分  • 市场影响度  • 风险评估  • 置信度计算         │
└─────────────────────────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────┐
│              投资建议层 (Investment Recommendation)          │
│  • 股票关联  • 短期评估  • 风险等级  • 操作建议             │
└─────────────────────────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────┐
│            向量相似性层 (ChromaDB Semantic Search)          │
│  • 语义相似性  • 历史对比  • 事件聚类  • 趋势发现           │
└─────────────────────────────────────────────────────────────┘
```

## 数据库设计 (当前实现)

### 核心表结构
```sql
-- 股票基础信息 (支持多市场)
ticker: id, code, name, group_id, market, status, create_time

-- 股票评分数据 (支持多算法)
ticker_score: id, ticker_id, time_key, ma_buy, ma_sell, ma_score, 
              in_buy, in_sell, in_score, strategy_buy, strategy_sell, 
              strategy_score, score, history(JSON)

-- 新闻源配置
news_sources: id, name, source_type, url, status, weight, config(JSON)

-- 新闻文章 (包含AI分析)
news_articles: id, title, content, url, source_id, published_at,
               ai_analysis(JSON), sentiment_score, stock_relations(JSON)

-- 技术指标数据
ticker_indicator: id, ticker_id, time_key, indicator_key, value, history(JSON)

-- 投资策略数据
ticker_strategy: id, ticker_id, time_key, strategy_key, position, 
                 signal_strength, strategy_params(JSON)
```

### Pydantic模型特色
- **统一BaseModel**: 所有模型继承Pydantic BaseModel
- **三层结构**: Base → Create → Update → Full
- **类型安全**: 完整type hints和运行时验证
- **序列化支持**: to_dict()和from_dict()辅助函数
- **JSON字段**: history、config等复杂数据结构支持

## 核心技术实现模式

### 1. 数据提供者模式 (已完成)
```python
# 统一股票数据访问
from core.data_providers.stock_data_factory import get_stock_quote

# 自动选择最佳数据源并支持降级
response = get_stock_quote("600000", market=StockMarket.A_SHARE)
if response.success:
    stock_data = response.data
```

### 2. 雪球抽象层模式 (已重构)
```python
# 统一雪球客户端访问
from core.utils.xueqiu.xueqiu_client_factory import create_stock_client

async with create_stock_client() as client:
    # 统一的异步接口
    quote = await client.get_stock_quote_async("SH600000")
    company = await client.get_company_info_async("SH600000")
```

### 3. PocketFlow AI工作流 (已集成)
```python
# 基于PocketFlow的新闻分析流程
from core.ai_agents.news_analysis_flow import NewsAnalysisFlow

flow = NewsAnalysisFlow()
result = await flow.run({
    "news_content": article.content,
    "news_title": article.title,
    "source_weight": source.weight
})

# 获取结构化分析结果
analysis = result.get("analysis")
sentiment = result.get("sentiment_score") 
recommendations = result.get("investment_advice")
```

### 4. 评分系统标准化 (已完成)
```python
# 统一的List[TickerScore]返回类型
from core.score.trend_score import TrendScore

trend_scorer = TrendScore()
scores = trend_scorer.calculate(ticker, kl_data, strategy_data)
# scores: List[TickerScore] - 标准化返回类型

# 自动类型转换支持向后兼容
from core.data_source_helper import DataSourceHelper
helper = DataSourceHelper()
dict_scores = helper.convert_ticker_scores_to_dict(scores)
```

## 异步编程架构

### 异步优先设计
- **FastAPI**: 全异步API服务器
- **aiohttp**: 异步HTTP客户端
- **数据库操作**: 支持异步数据库操作
- **任务调度**: 异步后台任务处理
- **AI分析**: 异步LLM调用和向量计算

### 并发处理模式
```python
# 并发数据获取
import asyncio

async def fetch_multiple_sources(ticker_codes):
    tasks = [
        akshare_provider.get_stock_quote_async(code) 
        for code in ticker_codes
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]
```

## 部署架构

### Docker容器化
```yaml
# docker-compose.yml
services:
  investnote-api:
    build: .
    ports: ["8000:8000"]
    environment:
      - DB_TYPE=mysql
      - LLM_PROVIDER=qianwen
    volumes:
      - ./data:/app/data
      
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_DATABASE: investnote
      
  redis:
    image: redis:7.0
    ports: ["6379:6379"]
```

### 自动化部署
```bash
# deploy.sh - 支持版本管理和crontab同步
./deploy.sh v1.2.3  # 指定版本部署
# 自动备份旧crontab，部署新crontab，重启容器
```

## 监控与运维

### 健康检查
- **API健康检查**: `/health` 端点
- **数据库连接检查**: 实时连接状态监控
- **外部服务检查**: 数据源可用性监控
- **AI服务检查**: LLM服务响应状态

### 性能指标
- **响应时间**: API响应时间监控
- **数据源成功率**: 各数据源成功率统计
- **AI分析耗时**: LLM调用延迟跟踪
- **并发处理能力**: 异步任务处理性能

## 扩展性设计

### 模块化扩展
- **新数据源**: 实现DataProvider接口即可集成
- **新AI模型**: 基于PocketFlow添加新的工作流
- **新评分算法**: 继承BaseScore实现新算法
- **新市场支持**: 扩展StockMarket枚举和数据映射

### 向后兼容
- **API版本管理**: 路由版本控制
- **模型兼容**: Pydantic模型向前兼容
- **数据库迁移**: SQLAlchemy迁移脚本支持
- **配置兼容**: 环境变量和配置文件向前兼容 