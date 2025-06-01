#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
向量相似性计算工具
提供新闻相似性分析和聚类功能
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from collections import defaultdict

# 配置日志
logger = logging.getLogger(__name__)

class VectorSimilarityAnalyzer:
    """
    向量相似性分析器
    提供新闻文章的相似性计算和聚类分析
    """
    
    def __init__(self, similarity_threshold: float = 0.7):
        """
        初始化相似性分析器
        
        Args:
            similarity_threshold: 相似性阈值
        """
        self.similarity_threshold = similarity_threshold
        
    def calculate_similarity(self, 
                           vector1: List[float], 
                           vector2: List[float]) -> float:
        """
        计算两个向量的余弦相似度
        
        Args:
            vector1: 第一个向量
            vector2: 第二个向量
            
        Returns:
            float: 相似度分数 (0-1)
        """
        try:
            vec1 = np.array(vector1).reshape(1, -1)
            vec2 = np.array(vector2).reshape(1, -1)
            
            similarity = cosine_similarity(vec1, vec2)[0][0]
            return max(0.0, min(1.0, similarity))  # 确保在0-1范围内
            
        except Exception as e:
            logger.error(f"计算相似度失败: {e}")
            return 0.0
    
    def batch_similarity(self, 
                        query_vector: List[float],
                        vectors: List[List[float]]) -> List[float]:
        """
        批量计算查询向量与多个向量的相似度
        
        Args:
            query_vector: 查询向量
            vectors: 目标向量列表
            
        Returns:
            List[float]: 相似度分数列表
        """
        try:
            if not vectors:
                return []
            
            query_vec = np.array(query_vector).reshape(1, -1)
            target_vecs = np.array(vectors)
            
            similarities = cosine_similarity(query_vec, target_vecs)[0]
            return [max(0.0, min(1.0, sim)) for sim in similarities]
            
        except Exception as e:
            logger.error(f"批量相似度计算失败: {e}")
            return [0.0] * len(vectors)
    
    def find_similar_groups(self, 
                           articles: List[Dict[str, Any]],
                           min_similarity: float = None) -> List[List[Dict[str, Any]]]:
        """
        找到相似文章组
        
        Args:
            articles: 文章列表，每个包含 {id, title, content, embedding}
            min_similarity: 最小相似度阈值
            
        Returns:
            List[List[Dict]]: 相似文章组列表
        """
        if not articles:
            return []
        
        threshold = min_similarity or self.similarity_threshold
        similar_groups = []
        processed_ids = set()
        
        try:
            for i, article in enumerate(articles):
                if article['id'] in processed_ids:
                    continue
                
                current_group = [article]
                processed_ids.add(article['id'])
                
                # 查找与当前文章相似的其他文章
                for j, other_article in enumerate(articles[i+1:], i+1):
                    if other_article['id'] in processed_ids:
                        continue
                    
                    if 'embedding' in article and 'embedding' in other_article:
                        similarity = self.calculate_similarity(
                            article['embedding'], 
                            other_article['embedding']
                        )
                        
                        if similarity >= threshold:
                            current_group.append(other_article)
                            processed_ids.add(other_article['id'])
                
                # 只有包含多个文章的组才被认为是相似组
                if len(current_group) > 1:
                    similar_groups.append(current_group)
            
            logger.info(f"找到 {len(similar_groups)} 个相似文章组")
            return similar_groups
            
        except Exception as e:
            logger.error(f"查找相似组失败: {e}")
            return []
    
    def cluster_articles(self, 
                        articles: List[Dict[str, Any]],
                        n_clusters: Optional[int] = None,
                        max_clusters: int = 10) -> Dict[str, Any]:
        """
        对文章进行聚类分析
        
        Args:
            articles: 文章列表
            n_clusters: 聚类数量，None时自动确定
            max_clusters: 最大聚类数量
            
        Returns:
            Dict: 聚类结果
        """
        if not articles or len(articles) < 2:
            return {"clusters": [], "stats": {"total_articles": len(articles), "n_clusters": 0}}
        
        try:
            # 提取嵌入向量
            embeddings = []
            valid_articles = []
            
            for article in articles:
                if 'embedding' in article and article['embedding']:
                    embeddings.append(article['embedding'])
                    valid_articles.append(article)
            
            if len(embeddings) < 2:
                logger.warning("可用嵌入向量不足，无法进行聚类")
                return {"clusters": [], "stats": {"total_articles": len(articles), "n_clusters": 0}}
            
            # 确定聚类数量
            if n_clusters is None:
                n_clusters = min(max_clusters, max(2, len(embeddings) // 5))
            
            n_clusters = min(n_clusters, len(embeddings))
            
            # 执行K-means聚类
            X = np.array(embeddings)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(X)
            
            # 组织聚类结果
            clusters = defaultdict(list)
            for i, label in enumerate(cluster_labels):
                article_with_cluster = valid_articles[i].copy()
                article_with_cluster['cluster_id'] = int(label)
                clusters[int(label)].append(article_with_cluster)
            
            # 计算聚类统计信息
            cluster_stats = {}
            for cluster_id, cluster_articles in clusters.items():
                cluster_stats[cluster_id] = {
                    "size": len(cluster_articles),
                    "topics": self._extract_cluster_topics(cluster_articles),
                    "time_range": self._get_cluster_time_range(cluster_articles)
                }
            
            result = {
                "clusters": dict(clusters),
                "cluster_stats": cluster_stats,
                "stats": {
                    "total_articles": len(articles),
                    "clustered_articles": len(valid_articles),
                    "n_clusters": n_clusters,
                    "largest_cluster": max(len(cluster) for cluster in clusters.values()) if clusters else 0
                }
            }
            
            logger.info(f"聚类完成: {len(valid_articles)}篇文章分为{n_clusters}个聚类")
            return result
            
        except Exception as e:
            logger.error(f"聚类分析失败: {e}")
            return {"clusters": [], "stats": {"total_articles": len(articles), "n_clusters": 0}}
    
    def _extract_cluster_topics(self, articles: List[Dict[str, Any]]) -> List[str]:
        """提取聚类的主要话题"""
        try:
            # 简单的关键词统计
            word_count = defaultdict(int)
            
            for article in articles:
                title = article.get('title', '')
                content = article.get('content', '')
                
                # 简单的中文分词（这里使用简单的方法，实际项目中可以使用jieba等）
                text = f"{title} {content}".lower()
                words = text.split()
                
                for word in words:
                    if len(word) > 1:  # 忽略单字符
                        word_count[word] += 1
            
            # 返回频率最高的前5个词
            top_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:5]
            return [word for word, count in top_words]
            
        except Exception as e:
            logger.error(f"提取聚类话题失败: {e}")
            return []
    
    def _get_cluster_time_range(self, articles: List[Dict[str, Any]]) -> Dict[str, str]:
        """获取聚类的时间范围"""
        try:
            timestamps = []
            
            for article in articles:
                if 'created_at' in article:
                    try:
                        if isinstance(article['created_at'], str):
                            timestamp = datetime.fromisoformat(article['created_at'].replace('Z', '+00:00'))
                        else:
                            timestamp = article['created_at']
                        timestamps.append(timestamp)
                    except Exception:
                        continue
            
            if timestamps:
                min_time = min(timestamps)
                max_time = max(timestamps)
                return {
                    "start": min_time.isoformat(),
                    "end": max_time.isoformat(),
                    "span_hours": (max_time - min_time).total_seconds() / 3600
                }
            
            return {"start": "", "end": "", "span_hours": 0}
            
        except Exception as e:
            logger.error(f"获取时间范围失败: {e}")
            return {"start": "", "end": "", "span_hours": 0}
    
    def detect_trending_topics(self, 
                              articles: List[Dict[str, Any]],
                              time_window_hours: int = 24) -> List[Dict[str, Any]]:
        """
        检测趋势话题
        
        Args:
            articles: 文章列表
            time_window_hours: 时间窗口（小时）
            
        Returns:
            List[Dict]: 趋势话题列表
        """
        try:
            if not articles:
                return []
            
            # 过滤时间窗口内的文章
            cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
            recent_articles = []
            
            for article in articles:
                if 'created_at' in article:
                    try:
                        if isinstance(article['created_at'], str):
                            article_time = datetime.fromisoformat(article['created_at'].replace('Z', '+00:00'))
                        else:
                            article_time = article['created_at']
                        
                        if article_time >= cutoff_time:
                            recent_articles.append(article)
                    except Exception:
                        continue
            
            if len(recent_articles) < 2:
                return []
            
            # 对最近文章进行聚类
            clustering_result = self.cluster_articles(recent_articles, max_clusters=5)
            
            # 转换为趋势话题格式
            trending_topics = []
            for cluster_id, cluster_articles in clustering_result.get('clusters', {}).items():
                if len(cluster_articles) >= 2:  # 至少2篇文章才算趋势
                    cluster_stats = clustering_result.get('cluster_stats', {}).get(cluster_id, {})
                    
                    trending_topics.append({
                        "topic_id": f"trend_{cluster_id}",
                        "keywords": cluster_stats.get('topics', []),
                        "article_count": len(cluster_articles),
                        "time_range": cluster_stats.get('time_range', {}),
                        "articles": cluster_articles[:5],  # 只返回前5篇代表文章
                        "trend_score": len(cluster_articles) / len(recent_articles)  # 简单的趋势分数
                    })
            
            # 按趋势分数排序
            trending_topics.sort(key=lambda x: x['trend_score'], reverse=True)
            
            logger.info(f"检测到 {len(trending_topics)} 个趋势话题")
            return trending_topics
            
        except Exception as e:
            logger.error(f"检测趋势话题失败: {e}")
            return []
    
    def analyze_article_evolution(self, 
                                 articles: List[Dict[str, Any]],
                                 topic_keywords: List[str]) -> Dict[str, Any]:
        """
        分析特定话题的文章演进
        
        Args:
            articles: 文章列表
            topic_keywords: 话题关键词
            
        Returns:
            Dict: 话题演进分析结果
        """
        try:
            # 过滤相关文章
            related_articles = []
            
            for article in articles:
                title = article.get('title', '').lower()
                content = article.get('content', '').lower()
                text = f"{title} {content}"
                
                # 检查是否包含话题关键词
                if any(keyword.lower() in text for keyword in topic_keywords):
                    related_articles.append(article)
            
            if not related_articles:
                return {"message": "未找到相关文章"}
            
            # 按时间排序
            related_articles.sort(key=lambda x: x.get('created_at', ''))
            
            # 分析时间分布
            time_distribution = defaultdict(int)
            for article in related_articles:
                if 'created_at' in article:
                    try:
                        if isinstance(article['created_at'], str):
                            timestamp = datetime.fromisoformat(article['created_at'].replace('Z', '+00:00'))
                        else:
                            timestamp = article['created_at']
                        
                        date_key = timestamp.strftime('%Y-%m-%d')
                        time_distribution[date_key] += 1
                    except Exception:
                        continue
            
            return {
                "topic_keywords": topic_keywords,
                "total_articles": len(related_articles),
                "time_span": {
                    "start": related_articles[0].get('created_at') if related_articles else None,
                    "end": related_articles[-1].get('created_at') if related_articles else None
                },
                "daily_distribution": dict(time_distribution),
                "peak_day": max(time_distribution.items(), key=lambda x: x[1]) if time_distribution else None,
                "recent_articles": related_articles[-5:] if len(related_articles) > 5 else related_articles
            }
            
        except Exception as e:
            logger.error(f"分析话题演进失败: {e}")
            return {"error": str(e)}

# 全局实例
_global_similarity_analyzer: Optional[VectorSimilarityAnalyzer] = None

def get_similarity_analyzer() -> VectorSimilarityAnalyzer:
    """获取全局相似性分析器实例"""
    global _global_similarity_analyzer
    if _global_similarity_analyzer is None:
        _global_similarity_analyzer = VectorSimilarityAnalyzer()
    return _global_similarity_analyzer 