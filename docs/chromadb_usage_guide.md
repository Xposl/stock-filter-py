# ChromaDB 向量数据库使用指南

## 概述

ChromaDB 是一个专为 AI 应用设计的开源向量数据库，在 InvestNote-py 项目中主要用于新闻文章的语义相似性分析和智能检索。

## 核心概念

### 1. 向量嵌入 (Vector Embeddings)
```python
# 文本转换为数字向量的过程
"苹果公司发布财报" → [0.1, 0.8, 0.3, ..., 0.7]  # 384维向量
"Apple releases earnings" → [0.2, 0.9, 0.4, ..., 0.6]  # 语义相似，向量接近
```

### 2. 相似性搜索
```python
# 基于向量距离计算语义相似度
query_vector = embed("投资机会")
similar_articles = find_similar(query_vector, threshold=0.5)
# 返回语义相似的文章，而非仅关键词匹配
```

### 3. 元数据过滤
```python
# 结合结构化数据进行复合查询
results = search(
    query="科技股分析",
    filters={"source": "财经日报", "date": "2024-06"}
)
```

## 项目中的使用

### 1. 基础初始化

```python
from core.ai_agents.vector_store import ChromaNewsStore, get_chroma_store

# 方式1: 直接实例化
store = ChromaNewsStore(
    db_path="./data/chroma_db",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    collection_name="news_articles"
)

# 方式2: 使用全局实例（推荐）
store = get_chroma_store()
```

### 2. 添加新闻文章

```python
# 单篇文章添加
success = await store.add_news_article(
    article_id=1,
    title="苹果公司Q4财报创新高",
    content="苹果公司发布2024年第四季度财报，营收达到1200亿美元...",
    source="财经新闻网",
    metadata={
        "category": "科技",
        "publish_date": "2024-06-01",
        "author": "张三"
    }
)

# 批量添加文章
articles = [
    {
        "id": 1,
        "title": "...",
        "content": "...",
        "source": "...",
        "metadata": {}
    },
    # 更多文章...
]

result = await store.batch_add_articles(articles, batch_size=50)
print(f"成功添加: {result['success']}, 失败: {result['failed']}")
```

### 3. 语义相似性搜索

```python
# 基础相似性搜索
results = await store.search_similar_articles(
    query_text="苹果公司财务表现",
    limit=10,
    similarity_threshold=0.5  # 相似度阈值 0-1
)

for article in results:
    print(f"标题: {article['title']}")
    print(f"相似度: {article['similarity_score']:.3f}")
    print(f"预览: {article['text_preview']}")
    print("-" * 50)
```

### 4. 关键词搜索

```python
# 基于关键词的向量搜索
results = await store.search_by_keywords(
    keywords=["AI", "人工智能", "机器学习"],
    limit=5
)
```

### 5. 文章管理

```python
# 获取特定文章
article = await store.get_article_by_id(article_id=1)
if article:
    print(f"文章标题: {article['title']}")
    print(f"文章内容: {article['content']}")

# 删除文章
deleted = await store.delete_article(article_id=1)
print(f"删除{'成功' if deleted else '失败'}")

# 获取统计信息
stats = store.get_collection_stats()
print(f"数据库中共有 {stats['document_count']} 篇文章")
```

## 实际应用场景

### 1. 新闻去重
```python
async def detect_duplicate_news(new_article):
    """检测重复新闻"""
    similar_articles = await store.search_similar_articles(
        query_text=f"{new_article['title']} {new_article['content']}",
        limit=3,
        similarity_threshold=0.85  # 高相似度阈值
    )
    
    if similar_articles:
        return True, similar_articles[0]  # 发现重复
    return False, None
```

### 2. 相关新闻推荐
```python
async def recommend_related_news(article_id, limit=5):
    """推荐相关新闻"""
    # 获取原文章
    article = await store.get_article_by_id(article_id)
    if not article:
        return []
    
    # 搜索相似文章
    similar = await store.search_similar_articles(
        query_text=article['content'],
        limit=limit + 1,  # +1 因为会包含自己
        similarity_threshold=0.3
    )
    
    # 过滤掉自己
    return [a for a in similar if a['article_id'] != article_id]
```

### 3. 投资主题分析
```python
async def analyze_investment_themes(query, days=30):
    """分析投资主题相关新闻"""
    results = await store.search_similar_articles(
        query_text=query,
        limit=20,
        similarity_threshold=0.4
    )
    
    # 按来源统计
    source_stats = {}
    for article in results:
        source = article['source']
        source_stats[source] = source_stats.get(source, 0) + 1
    
    return {
        "query": query,
        "total_articles": len(results),
        "source_distribution": source_stats,
        "articles": results
    }
```

### 4. 情感分析集成
```python
async def search_with_sentiment(query, sentiment_filter=None):
    """结合情感分析的搜索"""
    results = await store.search_similar_articles(query_text=query)
    
    if sentiment_filter:
        # 过滤特定情感的文章
        filtered_results = []
        for article in results:
            metadata = article.get('metadata', {})
            if metadata.get('sentiment') == sentiment_filter:
                filtered_results.append(article)
        return filtered_results
    
    return results
```

## 性能优化建议

### 1. 批量操作
```python
# ✅ 推荐: 批量添加
await store.batch_add_articles(articles, batch_size=50)

# ❌ 避免: 逐个添加
for article in articles:
    await store.add_news_article(...)  # 效率低
```

### 2. 合理设置阈值
```python
# 根据应用场景调整相似度阈值
similarity_threshold = {
    "新闻去重": 0.85,      # 高阈值，避免误删
    "相关推荐": 0.4,       # 中等阈值，平衡相关性
    "主题分析": 0.3,       # 低阈值，扩大范围
}
```

### 3. 文本预处理
```python
def preprocess_text(text):
    """优化文本预处理"""
    # 去除HTML标签
    import re
    text = re.sub(r'<[^>]+>', '', text)
    
    # 限制长度（避免过长文本影响性能）
    if len(text) > 1000:
        text = text[:1000] + "..."
    
    return text.strip()
```

## 监控和维护

### 1. 定期检查数据库状态
```python
async def health_check():
    """健康检查"""
    stats = store.get_collection_stats()
    
    if stats['status'] != 'healthy':
        logger.error(f"ChromaDB状态异常: {stats}")
        return False
    
    # 检查文档数量是否正常
    if stats['document_count'] == 0:
        logger.warning("ChromaDB中没有文档")
    
    return True
```

### 2. 数据清理
```python
async def cleanup_old_articles(days=90):
    """清理过期文章"""
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # 实现清理逻辑
    # 注意: 当前版本需要手动实现按日期清理
    pass
```

## 故障排除

### 1. 常见问题

**问题**: sentence-transformers模块未安装
```bash
# 解决方案
pip install sentence-transformers
```

**问题**: 嵌入模型加载失败
```python
# 检查模型路径和网络连接
store = ChromaNewsStore(
    embedding_model="sentence-transformers/all-MiniLM-L6-v2"  # 确保模型名称正确
)
```

**问题**: 相似性搜索结果为空
```python
# 检查相似度阈值设置
results = await store.search_similar_articles(
    query_text=query,
    similarity_threshold=0.1  # 降低阈值
)
```

### 2. 调试技巧

```python
# 启用详细日志
import logging
logging.getLogger('core.ai_agents.vector_store').setLevel(logging.DEBUG)

# 检查嵌入向量
embedding = await store._generate_embedding("测试文本")
print(f"向量维度: {embedding.shape}")
print(f"向量范围: {embedding.min():.3f} - {embedding.max():.3f}")
```

## 扩展功能

### 1. 多语言支持
```python
# 使用多语言嵌入模型
store = ChromaNewsStore(
    embedding_model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
```

### 2. 自定义相似度计算
```python
# 可以扩展 ChromaNewsStore 类来实现自定义相似度算法
class CustomChromaStore(ChromaNewsStore):
    def custom_similarity(self, query_embedding, doc_embeddings):
        # 实现自定义相似度计算
        pass
```

这个指南涵盖了 ChromaDB 在你的 InvestNote-py 项目中的主要使用方法。你可以根据具体需求进一步定制和优化。
