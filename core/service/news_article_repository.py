#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
新闻文章数据访问层
提供新闻文章的CRUD操作和相关业务逻辑
"""

import logging
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..models.news_article import NewsArticle, NewsArticleCreate, NewsArticleUpdate, news_article_to_dict, dict_to_news_article, ArticleStatus
from ..database.db_adapter import DbAdapter

logger = logging.getLogger(__name__)

class NewsArticleRepository:
    """新闻文章数据访问类"""
    
    def __init__(self):
        """
        初始化新闻文章仓库
        """
        self.db = DbAdapter()
    
    def _generate_url_hash(self, url: str) -> str:
        """
        生成URL哈希值用于去重
        
        Args:
            url: 文章URL
            
        Returns:
            URL的MD5哈希值
        """
        return hashlib.md5(url.encode('utf-8')).hexdigest()
    
    async def create_news_article(self, article: NewsArticleCreate) -> Optional[NewsArticle]:
        """
        创建新闻文章
        
        Args:
            article: 新闻文章创建模型
            
        Returns:
            创建成功的新闻文章模型，失败返回None
        """
        try:
            article_dict = news_article_to_dict(article)
            article_dict['created_at'] = datetime.now()
            article_dict['updated_at'] = datetime.now()
            article_dict['crawled_at'] = datetime.now()
            
            # 生成URL哈希值
            if 'url_hash' not in article_dict or not article_dict['url_hash']:
                article_dict['url_hash'] = self._generate_url_hash(article.url)
            
            # 设置默认值
            if 'content' not in article_dict:
                article_dict['content'] = None
            if 'summary' not in article_dict:
                article_dict['summary'] = None
            if 'author' not in article_dict:
                article_dict['author'] = None
            if 'category' not in article_dict:
                article_dict['category'] = None
            if 'published_at' not in article_dict:
                article_dict['published_at'] = None
            if 'entities' not in article_dict:
                article_dict['entities'] = None
            if 'keywords' not in article_dict:
                article_dict['keywords'] = None
            if 'sentiment_score' not in article_dict:
                article_dict['sentiment_score'] = None
            if 'topics' not in article_dict:
                article_dict['topics'] = None
            if 'importance_score' not in article_dict:
                article_dict['importance_score'] = 0.0
            if 'market_relevance_score' not in article_dict:
                article_dict['market_relevance_score'] = 0.0
            if 'processed_at' not in article_dict:
                article_dict['processed_at'] = None
            if 'error_message' not in article_dict:
                article_dict['error_message'] = None
            if 'word_count' not in article_dict:
                article_dict['word_count'] = 0
            if 'read_time_minutes' not in article_dict:
                article_dict['read_time_minutes'] = 0
            
            # 检查是否已存在相同URL的文章
            existing = await self.get_article_by_url_hash(article_dict['url_hash'])
            if existing:
                logger.warning(f"文章已存在: {article.url}")
                return existing
            
            sql = """
            INSERT INTO news_articles (
                title, url, url_hash, content, summary, author, source_id, source_name, category,
                published_at, crawled_at, language, region, entities, keywords, sentiment_score,
                topics, importance_score, market_relevance_score, status, processed_at,
                error_message, word_count, read_time_minutes, created_at, updated_at
            ) VALUES (
                :title, :url, :url_hash, :content, :summary, :author, :source_id, :source_name, :category,
                :published_at, :crawled_at, :language, :region, :entities, :keywords, :sentiment_score,
                :topics, :importance_score, :market_relevance_score, :status, :processed_at,
                :error_message, :word_count, :read_time_minutes, :created_at, :updated_at
            )
            """
            
            self.db.execute(sql, article_dict)
            self.db.commit()
            
            # 获取插入的记录
            result = await self.get_article_by_url_hash(article_dict['url_hash'])
            return result
            
        except Exception as e:
            logger.error(f"创建新闻文章失败: {e}")
            self.db.rollback()
            return None
    
    async def get_article_by_id(self, article_id: int) -> Optional[NewsArticle]:
        """
        根据ID获取新闻文章
        
        Args:
            article_id: 新闻文章ID
            
        Returns:
            新闻文章模型，未找到返回None
        """
        try:
            sql = "SELECT * FROM news_articles WHERE id = :id"
            result = self.db.query_one(sql, {"id": article_id})
            
            if result:
                return dict_to_news_article(result)
            return None
            
        except Exception as e:
            logger.error(f"获取新闻文章失败 (ID: {article_id}): {e}")
            return None
    
    async def get_article_by_url(self, url: str) -> Optional[NewsArticle]:
        """
        根据URL获取新闻文章
        
        Args:
            url: 文章URL
            
        Returns:
            新闻文章模型，未找到返回None
        """
        try:
            sql = "SELECT * FROM news_articles WHERE url = :url"
            result = self.db.query_one(sql, {"url": url})
            
            if result:
                return dict_to_news_article(result)
            return None
            
        except Exception as e:
            logger.error(f"获取新闻文章失败 (URL: {url}): {e}")
            return None
    
    async def get_article_by_url_hash(self, url_hash: str) -> Optional[NewsArticle]:
        """
        根据URL哈希获取新闻文章
        
        Args:
            url_hash: URL哈希值
            
        Returns:
            新闻文章模型，未找到返回None
        """
        try:
            sql = "SELECT * FROM news_articles WHERE url_hash = :url_hash"
            result = self.db.query_one(sql, {"url_hash": url_hash})
            
            if result:
                return dict_to_news_article(result)
            return None
            
        except Exception as e:
            logger.error(f"获取新闻文章失败 (URL Hash: {url_hash}): {e}")
            return None
    
    async def get_articles_by_source_id(self, source_id: int, limit: int = 100, offset: int = 0) -> List[NewsArticle]:
        """
        根据新闻源ID获取文章列表
        
        Args:
            source_id: 新闻源ID
            limit: 限制返回数量
            offset: 偏移量
            
        Returns:
            新闻文章列表
        """
        try:
            sql = """
            SELECT * FROM news_articles 
            WHERE source_id = :source_id 
            ORDER BY published_at DESC, crawled_at DESC 
            LIMIT :limit OFFSET :offset
            """
            results = self.db.query(sql, {
                "source_id": source_id,
                "limit": limit,
                "offset": offset
            })
            
            if results:
                return [dict_to_news_article(row) for row in results]
            return []
            
        except Exception as e:
            logger.error(f"获取新闻文章列表失败 (源ID: {source_id}): {e}")
            return []
    
    async def get_articles_by_status(self, status: ArticleStatus, limit: int = 100, offset: int = 0) -> List[NewsArticle]:
        """
        根据状态获取文章列表
        
        Args:
            status: 文章状态
            limit: 限制返回数量
            offset: 偏移量
            
        Returns:
            新闻文章列表
        """
        try:
            sql = """
            SELECT * FROM news_articles 
            WHERE status = :status 
            ORDER BY crawled_at DESC 
            LIMIT :limit OFFSET :offset
            """
            results = self.db.query(sql, {
                "status": status.value,
                "limit": limit,
                "offset": offset
            })
            
            if results:
                return [dict_to_news_article(row) for row in results]
            return []
            
        except Exception as e:
            logger.error(f"获取新闻文章列表失败 (状态: {status}): {e}")
            return []
    
    async def get_recent_articles(self, hours: int = 24, limit: int = 100) -> List[NewsArticle]:
        """
        获取最近的新闻文章
        
        Args:
            hours: 最近多少小时内的文章
            limit: 限制返回数量
            
        Returns:
            新闻文章列表
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            sql = """
            SELECT * FROM news_articles 
            WHERE crawled_at >= :cutoff_time 
            ORDER BY importance_score DESC, published_at DESC, crawled_at DESC 
            LIMIT :limit
            """
            results = self.db.query(sql, {
                "cutoff_time": cutoff_time,
                "limit": limit
            })
            
            if results:
                return [dict_to_news_article(row) for row in results]
            return []
            
        except Exception as e:
            logger.error(f"获取最近新闻文章失败: {e}")
            return []
    
    async def search_articles(self, query: str, limit: int = 50, offset: int = 0) -> List[NewsArticle]:
        """
        搜索新闻文章
        
        Args:
            query: 搜索关键词
            limit: 限制返回数量
            offset: 偏移量
            
        Returns:
            新闻文章列表
        """
        try:
            search_term = f"%{query}%"
            sql = """
            SELECT * FROM news_articles 
            WHERE title LIKE :query OR content LIKE :query OR summary LIKE :query
            ORDER BY importance_score DESC, published_at DESC 
            LIMIT :limit OFFSET :offset
            """
            results = self.db.query(sql, {
                "query": search_term,
                "limit": limit,
                "offset": offset
            })
            
            if results:
                return [dict_to_news_article(row) for row in results]
            return []
            
        except Exception as e:
            logger.error(f"搜索新闻文章失败: {e}")
            return []
    
    async def query_articles(
        self, 
        page: int = 1, 
        page_size: int = 20, 
        search: Optional[str] = None,
        source_id: Optional[int] = None,
        hours: Optional[int] = None,
        status: Optional[str] = None
    ) -> tuple[List[NewsArticle], int]:
        """
        综合查询新闻文章
        
        Args:
            page: 页码（从1开始）
            page_size: 每页数量
            search: 搜索关键词
            source_id: 新闻源ID筛选
            hours: 时间范围筛选（小时）
            status: 状态筛选
            
        Returns:
            (文章列表, 总数)
        """
        try:
            # 构建查询条件
            where_clauses = []
            params = {}
            
            # 时间筛选
            if hours:
                cutoff_time = datetime.now() - timedelta(hours=hours)
                where_clauses.append("crawled_at >= :cutoff_time")
                params["cutoff_time"] = cutoff_time
            
            # 新闻源筛选
            if source_id:
                where_clauses.append("source_id = :source_id")
                params["source_id"] = source_id
            
            # 状态筛选
            if status:
                where_clauses.append("status = :status")
                params["status"] = status
            
            # 搜索筛选
            if search:
                search_term = f"%{search}%"
                where_clauses.append("(title LIKE :search OR content LIKE :search OR summary LIKE :search)")
                params["search"] = search_term
            
            # 构建WHERE子句
            where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            # 查询总数
            count_sql = f"SELECT COUNT(*) as total FROM news_articles {where_clause}"
            count_result = self.db.query_one(count_sql, params)
            total = count_result['total'] if count_result else 0
            
            # 查询数据
            offset = (page - 1) * page_size
            params.update({
                "limit": page_size,
                "offset": offset
            })
            
            data_sql = f"""
            SELECT * FROM news_articles 
            {where_clause}
            ORDER BY importance_score DESC, published_at DESC, crawled_at DESC 
            LIMIT :limit OFFSET :offset
            """
            
            results = self.db.query(data_sql, params)
            
            articles = []
            if results:
                articles = [dict_to_news_article(row) for row in results]
            
            return articles, total
            
        except Exception as e:
            logger.error(f"查询新闻文章失败: {e}")
            return [], 0
    
    async def update_news_article(self, article_id: int, update_data: NewsArticleUpdate) -> Optional[NewsArticle]:
        """
        更新新闻文章
        
        Args:
            article_id: 新闻文章ID
            update_data: 更新数据
            
        Returns:
            更新后的新闻文章模型，失败返回None
        """
        try:
            # 获取当前文章
            current_article = await self.get_article_by_id(article_id)
            if not current_article:
                logger.warning(f"新闻文章不存在: {article_id}")
                return None
            
            # 准备更新数据
            update_dict = news_article_to_dict(update_data)
            if not update_dict:
                logger.warning("没有提供更新数据")
                return current_article
            
            update_dict['updated_at'] = datetime.now()
            
            # 构建更新SQL
            set_clauses = []
            params = {"id": article_id}
            
            for key, value in update_dict.items():
                set_clauses.append(f"{key} = :{key}")
                params[key] = value
            
            sql = f"UPDATE news_articles SET {', '.join(set_clauses)} WHERE id = :id"
            
            self.db.execute(sql, params)
            self.db.commit()
            
            # 返回更新后的文章
            return await self.get_article_by_id(article_id)
            
        except Exception as e:
            logger.error(f"更新新闻文章失败 (ID: {article_id}): {e}")
            self.db.rollback()
            return None
    
    async def update_article_processing_status(self, article_id: int, status: ArticleStatus, error_message: str = None) -> bool:
        """
        更新文章处理状态
        
        Args:
            article_id: 文章ID
            status: 新状态
            error_message: 错误信息（可选）
            
        Returns:
            更新是否成功
        """
        try:
            params = {
                "id": article_id,
                "status": status.value,
                "updated_at": datetime.now()
            }
            
            if status == ArticleStatus.PROCESSED:
                params["processed_at"] = datetime.now()
                params["error_message"] = None
                sql = """
                UPDATE news_articles 
                SET status = :status, processed_at = :processed_at, error_message = :error_message, updated_at = :updated_at
                WHERE id = :id
                """
            elif status == ArticleStatus.FAILED:
                params["error_message"] = error_message
                sql = """
                UPDATE news_articles 
                SET status = :status, error_message = :error_message, updated_at = :updated_at
                WHERE id = :id
                """
            else:
                sql = """
                UPDATE news_articles 
                SET status = :status, updated_at = :updated_at
                WHERE id = :id
                """
            
            self.db.execute(sql, params)
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"更新文章处理状态失败 (ID: {article_id}): {e}")
            self.db.rollback()
            return False
    
    async def batch_create_articles(self, articles: List[NewsArticleCreate]) -> List[NewsArticle]:
        """
        批量创建新闻文章
        
        Args:
            articles: 新闻文章创建模型列表
            
        Returns:
            成功创建的新闻文章列表
        """
        created_articles = []
        
        for article in articles:
            try:
                created = await self.create_news_article(article)
                if created:
                    created_articles.append(created)
            except Exception as e:
                logger.error(f"批量创建文章失败: {e}")
                continue
        
        return created_articles
    
    async def delete_old_articles(self, days: int = 30) -> int:
        """
        删除超过指定天数的旧文章
        
        Args:
            days: 保留天数
            
        Returns:
            删除的文章数量
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 先查询要删除的数量
            count_sql = "SELECT COUNT(*) as count FROM news_articles WHERE created_at < :cutoff_date"
            count_result = self.db.query_one(count_sql, {"cutoff_date": cutoff_date})
            deleted_count = count_result['count'] if count_result else 0
            
            # 执行删除
            sql = "DELETE FROM news_articles WHERE created_at < :cutoff_date"
            self.db.execute(sql, {"cutoff_date": cutoff_date})
            self.db.commit()
            
            logger.info(f"删除了 {deleted_count} 篇超过 {days} 天的旧文章")
            return deleted_count
            
        except Exception as e:
            logger.error(f"删除旧文章失败: {e}")
            self.db.rollback()
            return 0
    
    async def get_article_stats(self) -> Dict[str, Any]:
        """
        获取新闻文章统计信息
        
        Returns:
            统计信息字典
        """
        try:
            stats = {}
            
            # 按状态统计
            sql_status = """
            SELECT status, COUNT(*) as count 
            FROM news_articles 
            GROUP BY status
            """
            status_results = self.db.query(sql_status)
            stats['by_status'] = {row['status']: row['count'] for row in status_results} if status_results else {}
            
            # 按来源统计
            sql_source = """
            SELECT source_name, COUNT(*) as count 
            FROM news_articles 
            WHERE source_name IS NOT NULL
            GROUP BY source_name 
            ORDER BY count DESC 
            LIMIT 10
            """
            source_results = self.db.query(sql_source)
            stats['by_source'] = {row['source_name']: row['count'] for row in source_results} if source_results else {}
            
            # 今日文章数
            today = datetime.now().date()
            sql_today = "SELECT COUNT(*) as count FROM news_articles WHERE DATE(crawled_at) = :today"
            today_result = self.db.query_one(sql_today, {"today": today})
            stats['today_count'] = today_result['count'] if today_result else 0
            
            # 总文章数
            sql_total = "SELECT COUNT(*) as total FROM news_articles"
            total_result = self.db.query_one(sql_total)
            stats['total_count'] = total_result['total'] if total_result else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"获取文章统计信息失败: {e}")
            return {} 