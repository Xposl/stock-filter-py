# InvestNote 定时新闻抓取配置指南

## 概述

本文档介绍如何配置 InvestNote 系统的定时新闻抓取功能。系统提供了两种定时任务方式：

1. **内置调度器（推荐）**：使用 APScheduler 实现的内置定时任务
2. **系统 Cron**：使用系统级别的 crontab 定时任务

## 方式一：内置调度器（推荐）

### 1. 启动调度器

通过 API 启动内置调度器：

```bash
# 启动调度器
curl -X POST http://localhost:8000/investnote/cron/news/scheduler/start

# 查看调度器状态
curl http://localhost:8000/investnote/cron/news/scheduler
```

### 2. 默认定时任务

内置调度器包含以下默认定时任务：

| 任务名称 | 时间 | 频率 | 说明 |
|---------|------|------|------|
| 晨间新闻抓取 | 8:00 | 每天 | 获取晨间财经新闻 |
| 每小时新闻抓取 | 9:00-18:00 | 每小时 | 工作时间定时抓取 |
| 交易时间新闻抓取 | 9:00-15:00 | 每30分钟 | 交易时间高频抓取 |
| 收盘新闻抓取 | 18:00 | 每天 | 获取收盘后新闻 |

### 3. 手动触发

可以随时手动触发新闻抓取：

```bash
# 手动触发新闻抓取
curl -X POST http://localhost:8000/investnote/cron/news/manual

# 后台任务触发（异步）
curl -X POST http://localhost:8000/investnote/cron/news \
  -H "Content-Type: application/json" \
  -d '{"limit": 100}'
```

## 方式二：系统 Cron 任务

### 1. 脚本准备

确保脚本有执行权限：

```bash
chmod +x scripts/cron_news_fetch.sh
```

### 2. 测试脚本

```bash
# 测试API健康检查
./scripts/cron_news_fetch.sh health

# 测试新闻抓取
./scripts/cron_news_fetch.sh fetch

# 查看抓取状态
./scripts/cron_news_fetch.sh status
```

### 3. 配置 Crontab

编辑 crontab：

```bash
crontab -e
```

添加以下定时任务：

```bash
# InvestNote 新闻抓取定时任务

# 每30分钟抓取一次（工作时间 9:00-18:00）
*/30 9-18 * * 1-5 /path/to/investnote/scripts/cron_news_fetch.sh

# 每小时抓取一次（非工作时间）
0 19-23,0-8 * * * /path/to/investnote/scripts/cron_news_fetch.sh

# 晨间新闻（每天 8:00）
0 8 * * * /path/to/investnote/scripts/cron_news_fetch.sh

# 收盘新闻（工作日 18:30）
30 18 * * 1-5 /path/to/investnote/scripts/cron_news_fetch.sh
```

### 4. 高级 Cron 配置

```bash
# 高频交易时间抓取（9:30-15:00 每15分钟）
*/15 9-14 * * 1-5 /path/to/investnote/scripts/cron_news_fetch.sh
30 15 * * 1-5 /path/to/investnote/scripts/cron_news_fetch.sh

# 周末新闻抓取（每2小时）
0 */2 * * 0,6 /path/to/investnote/scripts/cron_news_fetch.sh

# 节假日新闻抓取（每小时）
0 * * * * /path/to/investnote/scripts/cron_news_fetch.sh
```

## API 接口详细说明

### 1. 新闻抓取接口

#### POST `/cron/news`
触发后台新闻抓取任务

**请求参数：**
```json
{
  "source_ids": [1, 2, 3],  // 可选：指定新闻源ID
  "limit": 100              // 可选：返回文章数量限制
}
```

**响应示例：**
```json
{
  "status": "success",
  "message": "新闻抓取任务已启动",
  "task_info": {
    "source_ids": "all_active",
    "limit": 100,
    "started_at": "2025-01-27T10:30:00"
  }
}
```

### 2. 新闻查询接口

#### GET `/news`
获取新闻文章列表

**查询参数：**
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认20）
- `search`: 搜索关键词
- `source_id`: 新闻源ID
- `hours`: 时间范围（小时，默认24）
- `status`: 文章状态

**响应示例：**
```json
{
  "status": "success",
  "data": {
    "total": 150,
    "page": 1,
    "page_size": 20,
    "articles": [
      {
        "id": 1,
        "title": "央行降准释放流动性",
        "url": "https://example.com/news/1",
        "content": "...",
        "published_at": "2025-01-27T09:30:00",
        "source_id": 1,
        "importance_score": 0.85,
        "stock_symbols": ["000001", "600000"]
      }
    ]
  }
}
```

### 3. 调度器管理接口

#### GET `/cron/news/scheduler`
获取调度器状态

```json
{
  "status": "success",
  "data": {
    "total_jobs": 4,
    "is_running": true,
    "jobs": [
      {
        "id": "morning_news_fetch",
        "name": "晨间新闻抓取",
        "next_run_time": "2025-01-28T08:00:00",
        "trigger": "cron[hour=8, minute=0]"
      }
    ]
  }
}
```

#### POST `/cron/news/scheduler/start`
启动调度器

#### POST `/cron/news/scheduler/stop`
停止调度器

## 监控和日志

### 1. 日志文件

系统 Cron 任务日志：
```bash
# 查看日志
tail -f /var/log/investnote/news_fetch.log

# 查看最近错误
grep "❌" /var/log/investnote/news_fetch.log
```

### 2. 监控接口

```bash
# 获取新闻抓取统计
curl http://localhost:8000/investnote/cron/news/status

# 获取新闻源状态
curl http://localhost:8000/investnote/news/sources
```

### 3. 健康检查

```bash
# API 健康检查
curl http://localhost:8000/investnote/

# 新闻系统健康检查
./scripts/cron_news_fetch.sh health
```

## 故障排除

### 1. 常见问题

**API 服务不可用**
```bash
# 检查 FastAPI 应用是否运行
ps aux | grep uvicorn

# 启动应用
uvicorn api.api:app --host 0.0.0.0 --port 8000
```

**数据库连接失败**
```bash
# 检查数据库配置
echo $DATABASE_URL

# 初始化数据库
python tools/news_db_init.py
```

**新闻源访问失败**
```bash
# 测试新闻源连通性
python -c "
import asyncio
from core.news_aggregator.rss_aggregator import RSSAggregator
asyncio.run(RSSAggregator().test_connection('https://cn.investing.com/rss/news.rss'))
"
```

### 2. 调试模式

启动应用时启用调试模式：

```bash
# 启用详细日志
uvicorn api.api:app --host 0.0.0.0 --port 8000 --log-level debug

# 检查新闻聚合器状态
python tools/test_news_system.py
```

## 最佳实践

### 1. 定时策略建议

- **开盘前（8:00-9:00）**：获取晨间新闻和市场预期
- **交易时间（9:30-15:00）**：高频抓取（每15-30分钟）
- **收盘后（15:30-18:00）**：获取收盘分析和业绩公告
- **非交易时间**：降低频率（每1-2小时）

### 2. 性能优化

- 根据服务器性能调整抓取频率
- 监控数据库存储空间
- 定期清理过期新闻数据
- 使用缓存减少重复抓取

### 3. 数据质量

- 定期检查新闻源可用性
- 监控重复文章去重效果
- 验证股票符号提取准确性
- 关注重要性评分合理性

## 扩展配置

### 1. 添加新闻源

通过数据库或API添加新的新闻源：

```sql
INSERT INTO news_source (name, url, source_type, status) 
VALUES ('新财经网', 'https://example.com/rss', 'RSS', 'ACTIVE');
```

### 2. 自定义定时任务

可以通过代码添加自定义定时任务：

```python
scheduler = await get_news_scheduler()
scheduler.add_custom_job(
    func=custom_fetch_function,
    trigger_type="cron",
    hour=10,
    minute=30
)
```

### 3. 集成通知

可以集成邮件、微信、钉钉等通知：

```bash
# 在 cron 脚本中添加通知
if ! ./scripts/cron_news_fetch.sh; then
    echo "新闻抓取失败" | mail -s "InvestNote Alert" admin@example.com
fi
``` 