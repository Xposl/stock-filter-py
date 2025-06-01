# InvestNote-py 开发任务跟踪

## 当前状态：系统优化和架构重构阶段 🏗️

### 🎨 创意阶段完成 (2025.01.27)

#### ✅ 创意设计决策记录

**1. 雪球数据抽象层架构 - 分层抽象模式**
- **设计决策**: 创建XueqiuBaseClient基类，XueqiuNewsClient和XueqiuStockClient分别继承
- **核心优势**: 消除代码重复，清晰职责分离，为akshare集成做准备
- **实现要点**: 统一会话管理、令牌获取策略、异步/同步接口适配

**2. AKShare数据优先策略 - 策略模式+工厂方法**
- **设计决策**: AKShare作为主要数据源，雪球API作为补充，使用策略模式管理
- **核心优势**: 充分利用akshare开源优势，支持运行时策略切换
- **实现要点**: 统一IStockDataProvider接口，智能降级策略，性能优化

**3. 投资机会检测算法 - 混合智能系统（规则+AI）**
- **设计决策**: 规则引擎快速筛选 + AI模型深度分析的分层处理
- **核心优势**: 平衡性能和准确性，规则层提供可解释性
- **实现要点**: 多因子评分模型，支持不同投资策略，实时性保证

**4. FastAPI规则体系重组 - 分层次目录结构**
- **设计决策**: Core/Patterns/Guidelines/Tools/Examples五层结构
- **核心优势**: 与Memory Bank一致，支持按需加载，优化token使用
- **实现要点**: 智能索引系统，版本管理，保持向后兼容

### 🚀 已完成任务 (2025.01.27 更新)

#### ✅ 0. 雪球数据抽象层实现 (优先级：最高) ⭐ 新完成
**完成时间**: 2025.01.27

**已完成**:
- ✅ **XueqiuBaseClient基类**: [core/utils/xueqiu/xueqiu_base_client.py](mdc:core/utils/xueqiu/xueqiu_base_client.py)
  - 统一会话管理和令牌获取策略（pyppeteer + urllib备用）
  - 同步/异步HTTP请求抽象
  - 错误处理和重试机制
  - 客户端类型抽象方法

- ✅ **XueqiuNewsClient新闻客户端**: [core/utils/xueqiu/xueqiu_news_client.py](mdc:core/utils/xueqiu/xueqiu_news_client.py)
  - 继承XueqiuBaseClient，专门处理新闻聚合
  - 时间线数据抓取和解析
  - 股票符号提取和重要性评分
  - 完整的NewsArticle转换

- ✅ **XueqiuStockClient股票客户端**: [core/utils/xueqiu/xueqiu_stock_client.py](mdc:core/utils/xueqiu/xueqiu_stock_client.py)
  - 继承XueqiuBaseClient，专门处理股票数据
  - 股票报价、公司信息和历史数据
  - 支持A股（SH/SZ）、港股（HK）、美股
  - 同步和异步版本接口

- ✅ **XueqiuClientFactory工厂**: [core/utils/xueqiu/xueqiu_client_factory.py](mdc:core/utils/xueqiu/xueqiu_client_factory.py)
  - 统一创建和管理雪球客户端
  - 支持配置共享和会话管理
  - create_news_client() 和 create_stock_client() 便捷函数

- ✅ **现有代码重构**:
  - 更新 [core/news_aggregator/xueqiu_aggregator.py](mdc:core/news_aggregator/xueqiu_aggregator.py) 使用新的抽象层
  - 更新 [core/utils/xueqiu/xueqiu_api.py](mdc:core/utils/xueqiu/xueqiu_api.py) 使用新的抽象层
  - 保留向后兼容性和现有方法签名

**技术特点**:
- **抽象层设计**: 统一会话管理、令牌处理、错误重试
- **职责分离**: 新闻和股票客户端各司其职
- **向后兼容**: 现有代码无需大幅修改即可使用新抽象层
- **异步支持**: 完整的同步和异步接口

#### ✅ 0.1. AKShare数据源集成 (优先级：最高) ⭐ 新完成
**完成时间**: 2025.01.27

**已完成**:
- ✅ **akshare依赖升级**: 升级到 akshare-1.16.96 版本

- ✅ **StockDataProvider接口**: [core/data_providers/stock_data_provider.py](mdc:core/data_providers/stock_data_provider.py)
  - 统一的股票数据访问抽象接口
  - 支持多市场（StockMarket枚举：A股、港股、美股、英股）
  - 标准化数据周期（DataPeriod枚举：分钟、小时、日、周、月线）
  - 错误处理和优先级管理
  - StockDataResponse统一响应格式

- ✅ **AKShareProvider实现**: [core/data_providers/akshare_provider.py](mdc:core/data_providers/akshare_provider.py)
  - 基于akshare库的数据提供者，最高优先级（100）
  - 支持A股、港股、美股三个市场
  - 实现全部接口：股票信息、实时行情、历史数据、公司信息、股票搜索
  - 自动市场检测和股票代码标准化
  - 完善的错误处理和数据格式转换

- ✅ **XueqiuProvider实现**: [core/data_providers/xueqiu_provider.py](mdc:core/data_providers/xueqiu_provider.py)
  - 基于雪球API的数据提供者，中等优先级（50）
  - 作为AKShare的补充数据源
  - 使用重构后的雪球客户端抽象层
  - 支持同步和异步操作

- ✅ **StockDataFactory策略管理**: [core/data_providers/stock_data_factory.py](mdc:core/data_providers/stock_data_factory.py)
  - 策略模式管理多个数据提供者
  - 智能提供者选择和自动降级
  - 错误计数和可用性管理
  - 提供者状态监控和重置功能
  - 全局工厂实例和便捷函数封装

- ✅ **综合测试验证**: [test_stock_data_integration.py](mdc:test_stock_data_integration.py)
  - 完整的集成测试脚本
  - 验证AKShare和雪球数据源功能
  - 测试自动选择和降级策略
  - 多市场支持验证
  - 提供者状态监控测试

**技术特点**:
- **策略模式**: 支持运行时数据源切换和智能降级
- **优先级管理**: AKShare优先，雪球补充，错误自动降级
- **统一接口**: 标准化的股票数据访问方式
- **多市场支持**: A股、港股、美股统一处理
- **性能优化**: 错误缓存、连接复用、智能重试

#### ✅ 0.2. Cursor规则体系更新完成 (优先级：最高) ⭐ 新完成
**完成时间**: 2025.01.27

**已完成**:
- ✅ **数据提供者架构设计规范**: [data_provider_architecture.mdc](mdc:.cursor/rules/fast-api/data_provider_architecture.mdc)
  - 完整的数据提供者层（Data Provider Layer）架构文档
  - 雪球抽象层（Xueqiu Abstraction Layer）设计说明
  - 架构层次图和数据流转示意图
  - 智能降级策略和错误处理机制
  - 代码重构对比和迁移指南
  - 性能优化、扩展性设计和未来规划

- ✅ **项目结构规范更新**: [project_structure.mdc](mdc:.cursor/rules/fast-api/project_structure.mdc)
  - 新增数据提供者层目录结构 (`core/data_providers/`)
  - 新增雪球抽象层目录结构 (`core/utils/xueqiu/`)
  - 更新架构层次说明和模块依赖关系
  - 重构后的新闻聚合模块说明

- ✅ **编码规范更新**: [code_guidelines.mdc](mdc:.cursor/rules/fast-api/code_guidelines.mdc)
  - 新增数据提供者层编码规范（抽象接口、AKShare提供者、工厂模式）
  - 新增雪球抽象层编码规范（基础客户端、专业客户端、工厂模式）
  - 重构代码适配规范和向后兼容性原则
  - 现有代码迁移指南和最佳实践

- ✅ **主规则文档更新**: [rules-document.mdc](mdc:.cursor/rules/rules-document.mdc)
  - 新增数据提供者架构设计规范索引
  - 更新项目结构和编码规范的新增内容说明
  - 添加架构重构成果总结（技术优势、性能优势、运维优势）
  - 更新Memory Bank文件结构说明
  - 新增使用指南和发展规划
  - 完善注意事项和向后兼容性说明

**更新要点**:
- **文档完整性**: 新增专门的架构设计文档，详细说明重构方案
- **索引更新**: 主规则文档正确引用所有新增和更新的规范文件
- **实施指南**: 提供具体的代码使用示例和迁移指南
- **成果总结**: 完整记录架构重构的技术成果和业务价值
- **未来规划**: 明确后续发展方向和扩展计划

#### ✅ 1. Memory Bank规则体系更新
- **项目结构规范更新** ([project_structure.mdc](mdc:.cursor/rules/fast-api/project_structure.mdc))
  - 基于实际代码库重新设计结构文档
  - 反映三层架构：API → Handler → Repository → Model
  - 增加新闻聚合、AI代理等新模块说明
- **编码规范更新** ([code_guidelines.mdc](mdc:.cursor/rules/fast-api/code_guidelines.mdc))
  - 适配InvestNote-py的业务场景
  - 明确Handler、Repository、Model层的职责和编码规范
  - 新增新闻处理、AI代理模块的编码标准
- **技术上下文更新** ([techContext.md](mdc:memory-bank/techContext.md))
  - 基于实际代码结构重新梳理技术栈
  - 区分已实现功能与待实现功能
  - 完善新增依赖和架构设计

#### ✅ 2. 依赖管理更新
- **requirements.txt扩展** ([requirements.txt](mdc:requirements.txt))
  - 添加AI/NLP相关依赖：openai, langchain, spacy, nltk, sentence-transformers
  - 添加任务队列依赖：celery, redis
  - 添加新闻处理依赖：feedparser, newspaper3k, readability, lxml_html_clean
  - 添加向量数据库：chromadb, faiss-cpu
  - 添加数据库异步支持：aiosqlite

#### ✅ 3. 数据模型设计与实现
- **新闻源模型** ([core/models/news_source.py](mdc:core/models/news_source.py))
  - 支持RSS、API、网站等多种源类型
  - 完整的过滤配置和状态管理
  - JSON字段的属性访问器
- **新闻文章模型** ([core/models/news_article.py](mdc:core/models/news_article.py))
  - 完整的文章存储结构
  - NLP处理结果字段（实体、关键词、情感分析、主题）
  - 重要性和市场相关性评分
  - 修复Base导入问题，确保表正确创建

#### ✅ 4. RSS新闻聚合器实现
- **RSSAggregator类** ([core/news_aggregator/rss_aggregator.py](mdc:core/news_aggregator/rss_aggregator.py))
  - 异步RSS内容抓取
  - 多字段内容解析（标题、摘要、正文、作者、分类）
  - 智能过滤和时间范围控制
  - 全文内容提取（newspaper3k集成）
  - URL去重和内容清理
  - **SSL证书问题修复** - 添加宽松SSL配置，解决英为财情等HTTPS源访问问题

#### ✅ 5. 雪球新闻聚合器实现
- **XueqiuAggregator类** ([core/news_aggregator/xueqiu_aggregator.py](mdc:core/news_aggregator/xueqiu_aggregator.py))
  - 专门处理雪球平台投资动态
  - 股票代码自动识别和提取
  - 基于互动数据的重要性评分
  - 用户信息和时间解析
  - 内容过滤和质量控制

#### ✅ 6. 数据库初始化完善
- **新闻数据库初始化脚本** ([core/database/news_db_init.py](mdc:core/database/news_db_init.py))
  - 完整的表创建和删除方法
  - **优化的默认新闻源配置**：
    - 英为财情RSS源（综合新闻、股票新闻、经济新闻）✅ 测试通过
    - 新浪财经、财新网、东方财富、第一财经、华尔街见闻、Wind资讯
    - 雪球热门动态（API类型，暂停状态）
  - 数据库连接管理和异步支持
  - **测试验证通过** - 表创建、数据插入功能正常

#### ✅ 7. 新闻聚合管理器实现
- **NewsAggregatorManager类** ([core/news_aggregator/news_aggregator_manager.py](mdc:core/news_aggregator/news_aggregator_manager.py))
  - 统一管理RSS和API类型聚合器
  - 并发抓取多个新闻源
  - 自动保存文章到数据库
  - 新闻源状态更新和错误处理
  - 聚合统计信息和连通性测试

#### ✅ 8. MySQL数据库配置优化 (优先级：高)
**完成时间**: 2025.01.27

**已完成**:
- ✅ **依赖包更新**: 添加 `aiomysql==0.2.0` 和 `PyMySQL==1.1.0` 到 requirements.txt
- ✅ **数据库初始化脚本更新**: 
  - [tools/news_db_init.py](mdc:tools/news_db_init.py) 支持MySQL、PostgreSQL、SQLite三种数据库
  - 自动检测数据库类型并使用对应的SQL语法
  - 优先从环境变量 `DATABASE_URL` 读取配置
  - 提供各种数据库类型的配置示例
- ✅ **核心模块同步**: 更新 [core/database/news_db_init.py](mdc:core/database/news_db_init.py) 与tools版本保持一致
- ✅ **数据库配置规范文档**: 创建 [数据库配置规范](mdc:.cursor/rules/fast-api/database_configuration.mdc)
  - MySQL生产环境配置指南
  - 性能优化建议和索引策略
  - 备份和监控方案
  - 多环境配置管理
- ✅ **项目结构规范更新**: 在 [project_structure.mdc](mdc:.cursor/rules/fast-api/project_structure.mdc) 中增加数据库配置说明

**技术特点**:
- **多数据库兼容**: 支持MySQL(生产)、PostgreSQL(企业)、SQLite(开发)
- **环境变量驱动**: 统一通过 `DATABASE_URL` 管理配置
- **自动检测**: 根据连接字符串自动选择对应的数据库驱动和SQL语法
- **性能优化**: 提供连接池配置和索引策略建议

### 🔄 进行中任务

#### 📊 1. 新闻源优化和扩展 (优先级：高)
**进度**: 70% - 英为财情源已验证，需要优化其他源

**已验证可用**:
- ✅ 英为财情-综合新闻：https://cn.investing.com/rss/news.rss
- ✅ 英为财情-股票新闻：https://cn.investing.com/rss/news_285.rss

**需要修复/替换**:
- ❌ 第一财经：RSS链接404，需要查找新链接
- ❌ 网易财经：RSS链接404，需要查找新链接
- ⚠️ 新浪财经：连通但RSS格式问题
- ⚠️ 凤凰财经：连通但RSS格式问题

**待完成**:
- [ ] 查找和验证更多可用的中文财经RSS源
- [ ] 优化RSS解析器处理不同格式
- [ ] 实现雪球API聚合器的实际测试

#### 🔧 2. API集成和测试 (优先级：中)
**进度**: 20% - 基础框架已完成

**待完成**:
- [ ] 集成到FastAPI主应用
- [ ] 新闻源管理API端点
- [ ] 新闻文章查询API端点
- [ ] 聚合任务触发API

### 📋 待开始任务队列

#### 🏗️ 第一阶段：新闻聚合完善 (预计1-2周)

1. **新闻源扩展和优化** (3-5天)
   - 查找更多可用的中文财经RSS源
   - 实现雪球API的实际数据抓取
   - 添加英文财经新闻源（Bloomberg, Reuters, Financial Times）
   - 优化RSS解析器兼容性

2. **定时任务调度** (2-3天)
   - 实现基于Celery的定时新闻抓取
   - 配置不同新闻源的抓取频率
   - 错误重试和失败处理机制

3. **API集成** (2-3天)
   - 新闻管理API实现
   - 与现有认证系统集成
   - API文档和测试

#### 🤖 第二阶段：AI分析框架建设 (预计3-4周)

1. **AI代理基础框架** (1周)
   - BaseAgent抽象类实现
   - Agent注册和管理机制
   - 配置系统设计

2. **NLP工具模块** (1周)
   - 文本预处理工具
   - 实体识别器
   - 关键词提取
   - 情感分析

3. **第一个分析代理** (1-2周)
   - 行业影响分析Agent
   - 新闻重要性评分
   - 市场相关性判断

#### 🔍 第三阶段：投资机会检测 (预计2-3周)

1. **机会检测算法** (2周)
   - 新闻与股票关联算法
   - 影响链构建
   - 机会评分系统

2. **量化验证模块** (1周)
   - 资金流分析集成
   - 市场热度指标
   - 智能资金检测

#### ⚡ 第四阶段：异步处理和优化 (预计2-3周)

1. **Celery任务队列** (1周)
   - 任务定义和队列配置
   - 异步新闻处理
   - 后台AI分析

2. **缓存和性能优化** (1周)
   - Redis缓存策略
   - 数据库查询优化
   - API响应时间优化

3. **监控和告警** (1周)
   - 系统健康监控
   - 任务执行状态
   - 错误告警机制

### 🎯 里程碑计划

#### Milestone 1: 新闻聚合MVP (1周后) - 90%完成
- [x] 完整的新闻抓取流程
- [x] 基础的新闻管理API框架
- [x] 数据库完整初始化
- [x] 基本的监控和日志
- [ ] 更多可用新闻源验证

#### Milestone 2: AI分析初版 (5周后)
- [ ] 至少一个AI分析代理正常工作
- [ ] 新闻重要性自动评分
- [ ] 基础的投资洞察提取

#### Milestone 3: 机会检测原型 (9周后)
- [ ] 新闻驱动的投资机会识别
- [ ] 股票关联度计算
- [ ] 完整的机会推送流程

#### Milestone 4: 生产就绪版本 (13周后)
- [ ] 完整的异步处理流程
- [ ] 高性能和可扩展性
- [ ] 生产级监控和告警
- [ ] 完整的测试覆盖

### 🛠️ 技术债务与改进项目

#### 代码质量提升
- [ ] 统一异常处理机制
- [ ] 完善日志体系
- [ ] 代码覆盖率提升至80%+
- [ ] 性能基准测试建立

#### 架构优化
- [ ] 微服务化可行性评估
- [ ] 数据库读写分离
- [ ] API版本管理
- [ ] 配置热更新机制

#### 运维自动化
- [ ] CI/CD流水线建设
- [ ] 容器化部署优化
- [ ] 监控告警系统
- [ ] 自动化测试集成

### 📊 当前进度统计

**总体进度**: 25%
- ✅ 基础设施：85% (规则更新、数据模型、RSS聚合器、数据库初始化)
- 🔄 数据层：60% (数据库初始化完成、API框架搭建)
- ⏳ 业务层：5% (AI框架设计)
- ⏳ 应用层：0% (异步处理、优化)

**估计完成时间**: 12-14周 (基于单人开发，已提前2周)

**风险评估**: 
- 🟡 中等风险：LLM API稳定性和成本控制
- 🟢 低风险：新闻聚合基础功能已验证可行
- 🟡 中等风险：大规模新闻处理性能优化

### 🔄 下一步行动 (本周内)

1. **新闻源扩展和验证** (2-3天)
   - 查找第一财经、网易财经的新RSS链接
   - 测试更多英为财情的RSS分类源
   - 验证雪球API的实际可用性

2. **API集成** (2天)
   - 将新闻聚合功能集成到FastAPI主应用
   - 实现基础的新闻查询API

3. **定时任务设计** (1天)
   - 设计Celery任务结构
   - 规划不同新闻源的抓取策略

### 📈 成果总结

**本次实现的核心价值**:
1. **英为财情RSS源验证成功** - 解决了中文财经新闻的核心数据源问题
2. **完整的新闻聚合架构** - 支持RSS、API等多种数据源类型
3. **数据库基础设施完善** - 新闻存储和管理的完整解决方案
4. **SSL问题解决** - 为后续更多HTTPS新闻源接入扫清障碍

**技术突破**:
- 异步新闻抓取和处理流程
- 多类型聚合器统一管理
- 智能内容过滤和去重
- 完整的错误处理和状态管理

### 🔄 新增高优先级任务

#### 🏗️ 第零阶段：架构重构和优化 (预计2-3周) - 当前阶段

1. **雪球数据抽象层实现** (5-7天)
   - [ ] 实现XueqiuBaseClient基类（会话管理、令牌获取、HTTP封装）
   - [ ] 实现XueqiuNewsClient（继承基类，专注新闻聚合）
   - [ ] 实现XueqiuStockClient（继承基类，专注股票数据）
   - [ ] 创建XueqiuClientFactory（统一客户端创建）
   - [ ] 迁移现有代码到新抽象层
   - [ ] 编写单元测试和集成测试

2. **AKShare数据源集成** (5-7天)
   - [ ] 安装和配置akshare依赖（`pip install akshare --upgrade`）
   - [ ] 实现IStockDataProvider统一接口
   - [ ] 实现AKShareProvider（股票基础信息、实时行情、财务数据）
   - [ ] 实现StockDataFactory和策略选择逻辑
   - [ ] 实现数据源降级和健康监控
   - [ ] 性能测试和优化（批量查询、缓存策略）

3. **FastAPI规则体系重组** (3-4天)
   - [ ] 创建新的目录结构（Core/Patterns/Guidelines/Tools/Examples）
   - [ ] 重新组织现有规则文档
   - [ ] 创建index.mdc智能索引文件
   - [ ] 实现按需规则加载机制
   - [ ] 更新Memory Bank集成配置

4. **投资机会检测算法原型** (7-10天)
   - [ ] 实现规则引擎（关键词匹配、事件分类）
   - [ ] 集成NLP组件（jieba分词、情感分析、实体识别）
   - [ ] 实现多因子评分模型
   - [ ] 创建投资机会分类体系
   - [ ] 与现有新闻聚合系统集成
   - [ ] 构建测试数据集和验证机制 