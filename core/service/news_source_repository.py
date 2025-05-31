#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
新闻源数据访问层
提供新闻源的CRUD操作和相关业务逻辑
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.news_source import NewsSource, NewsSourceCreate, NewsSourceUpdate, news_source_to_dict, dict_to_news_source, NewsSourceStatus
from ..database.db_adapter import DbAdapter

logger = logging.getLogger(__name__)

class NewsSourceRepository:
    """新闻源数据访问类"""
    
    def __init__(self):
        """
        初始化新闻源仓库
        """
        self.db = DbAdapter()
    
    async def create_news_source(self, source: NewsSourceCreate) -> Optional[NewsSource]:
        """
        创建新闻源
        
        Args:
            source: 新闻源创建模型
            
        Returns:
            创建成功的新闻源模型，失败返回None
        """
        try:
            source_dict = news_source_to_dict(source)
            source_dict['created_at'] = datetime.now()
            source_dict['updated_at'] = datetime.now()
            
            # 设置默认值（确保字段都有值）
            if 'api_key' not in source_dict:
                source_dict['api_key'] = None
            if 'filter_keywords' not in source_dict:
                source_dict['filter_keywords'] = None
            if 'filter_categories' not in source_dict:
                source_dict['filter_categories'] = None
            if 'last_fetch_time' not in source_dict:
                source_dict['last_fetch_time'] = None
            if 'last_error_message' not in source_dict:
                source_dict['last_error_message'] = None
            if 'total_articles_fetched' not in source_dict:
                source_dict['total_articles_fetched'] = 0
            
            # 检查是否已存在相同名称的新闻源
            existing = await self.get_news_source_by_name(source.name)
            if existing:
                logger.warning(f"新闻源已存在: {source.name}")
                return existing  # 返回现有的而不是None
            
            # 调试：输出参数
            logger.debug(f"创建新闻源参数: {source_dict}")
            
            sql = """
            INSERT INTO news_sources (
                name, description, source_type, url, api_key,
                update_frequency, max_articles_per_fetch, filter_keywords, filter_categories,
                language, region, status, last_fetch_time, last_error_message,
                total_articles_fetched, created_at, updated_at
            ) VALUES (
                :name, :description, :source_type, :url, :api_key,
                :update_frequency, :max_articles_per_fetch, :filter_keywords, :filter_categories,
                :language, :region, :status, :last_fetch_time, :last_error_message,
                :total_articles_fetched, :created_at, :updated_at
            )
            """
            
            self.db.execute(sql, source_dict)
            self.db.commit()
            
            # 获取插入的记录
            result = await self.get_news_source_by_name(source.name)
            return result
            
        except Exception as e:
            logger.error(f"创建新闻源失败: {e}")
            self.db.rollback()
            return None
    
    async def get_news_source_by_id(self, source_id: int) -> Optional[NewsSource]:
        """
        根据ID获取新闻源
        
        Args:
            source_id: 新闻源ID
            
        Returns:
            新闻源模型，未找到返回None
        """
        try:
            sql = "SELECT * FROM news_sources WHERE id = :id"
            result = self.db.query_one(sql, {"id": source_id})
            
            if result:
                return dict_to_news_source(result)
            return None
            
        except Exception as e:
            logger.error(f"获取新闻源失败 (ID: {source_id}): {e}")
            return None
    
    async def get_news_source_by_name(self, name: str) -> Optional[NewsSource]:
        """
        根据名称获取新闻源
        
        Args:
            name: 新闻源名称
            
        Returns:
            新闻源模型，未找到返回None
        """
        try:
            sql = "SELECT * FROM news_sources WHERE name = :name"
            result = self.db.query_one(sql, {"name": name})
            
            if result:
                return dict_to_news_source(result)
            return None
            
        except Exception as e:
            logger.error(f"获取新闻源失败 (名称: {name}): {e}")
            return None
    
    async def get_news_sources_by_status(self, status: NewsSourceStatus) -> List[NewsSource]:
        """
        根据状态获取新闻源列表
        
        Args:
            status: 新闻源状态
            
        Returns:
            新闻源列表
        """
        try:
            sql = "SELECT * FROM news_sources WHERE status = :status ORDER BY created_at DESC"
            results = self.db.query(sql, {"status": status.value})
            
            if results:
                return [dict_to_news_source(row) for row in results]
            return []
            
        except Exception as e:
            logger.error(f"获取新闻源列表失败 (状态: {status}): {e}")
            return []
    
    async def get_all_news_sources(self, limit: int = 100, offset: int = 0) -> List[NewsSource]:
        """
        获取所有新闻源
        
        Args:
            limit: 限制返回数量
            offset: 偏移量
            
        Returns:
            新闻源列表
        """
        try:
            sql = "SELECT * FROM news_sources ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
            results = self.db.query(sql, {"limit": limit, "offset": offset})
            
            if results:
                return [dict_to_news_source(row) for row in results]
            return []
            
        except Exception as e:
            logger.error(f"获取所有新闻源失败: {e}")
            return []
    
    async def update_news_source(self, source_id: int, update_data: NewsSourceUpdate) -> Optional[NewsSource]:
        """
        更新新闻源
        
        Args:
            source_id: 新闻源ID
            update_data: 更新数据
            
        Returns:
            更新后的新闻源模型，失败返回None
        """
        try:
            # 获取当前新闻源
            current_source = await self.get_news_source_by_id(source_id)
            if not current_source:
                logger.warning(f"新闻源不存在: {source_id}")
                return None
            
            # 准备更新数据
            update_dict = news_source_to_dict(update_data)
            if not update_dict:
                logger.warning("没有提供更新数据")
                return current_source
            
            update_dict['updated_at'] = datetime.now()
            
            # 构建更新SQL
            set_clauses = []
            params = {"id": source_id}
            
            for key, value in update_dict.items():
                set_clauses.append(f"{key} = :{key}")
                params[key] = value
            
            sql = f"UPDATE news_sources SET {', '.join(set_clauses)} WHERE id = :id"
            
            self.db.execute(sql, params)
            self.db.commit()
            
            # 返回更新后的新闻源
            return await self.get_news_source_by_id(source_id)
            
        except Exception as e:
            logger.error(f"更新新闻源失败 (ID: {source_id}): {e}")
            self.db.rollback()
            return None
    
    async def update_last_fetch_info(self, source_id: int, error_message: str = None, article_count: int = 0) -> bool:
        """
        更新新闻源的最后抓取信息
        
        Args:
            source_id: 新闻源ID
            error_message: 错误信息，None表示成功
            article_count: 本次抓取的文章数量
            
        Returns:
            更新是否成功
        """
        try:
            params = {
                "id": source_id,
                "last_fetch_time": datetime.now(),
                "updated_at": datetime.now()
            }
            
            if error_message:
                # 有错误，更新状态为error
                params["status"] = NewsSourceStatus.ERROR.value
                params["last_error_message"] = error_message
                sql = """
                UPDATE news_sources 
                SET last_fetch_time = :last_fetch_time, 
                    status = :status,
                    last_error_message = :last_error_message,
                    updated_at = :updated_at
                WHERE id = :id
                """
            else:
                # 成功，清除错误信息，更新总数
                params["status"] = NewsSourceStatus.ACTIVE.value
                params["last_error_message"] = None
                sql = """
                UPDATE news_sources 
                SET last_fetch_time = :last_fetch_time,
                    status = :status,
                    last_error_message = :last_error_message,
                    total_articles_fetched = total_articles_fetched + :article_count,
                    updated_at = :updated_at
                WHERE id = :id
                """
                params["article_count"] = article_count
            
            self.db.execute(sql, params)
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"更新新闻源抓取信息失败 (ID: {source_id}): {e}")
            self.db.rollback()
            return False
    
    async def delete_news_source(self, source_id: int) -> bool:
        """
        删除新闻源
        
        Args:
            source_id: 新闻源ID
            
        Returns:
            删除是否成功
        """
        try:
            # 注意：这里应该考虑级联删除相关的新闻文章
            sql = "DELETE FROM news_sources WHERE id = :id"
            self.db.execute(sql, {"id": source_id})
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"删除新闻源失败 (ID: {source_id}): {e}")
            self.db.rollback()
            return False
    
    async def get_sources_for_update(self, max_sources: int = 50) -> List[NewsSource]:
        """
        获取需要更新的新闻源
        根据更新频率和最后抓取时间计算哪些源需要更新
        
        Args:
            max_sources: 最大返回数量
            
        Returns:
            需要更新的新闻源列表
        """
        try:
            # SQLite和MySQL兼容的SQL - 计算下次更新时间
            sql = """
            SELECT * FROM news_sources 
            WHERE status = :status 
            AND (
                last_fetch_time IS NULL 
                OR datetime(last_fetch_time, '+' || update_frequency || ' seconds') <= datetime('now')
            )
            ORDER BY 
                CASE WHEN last_fetch_time IS NULL THEN 0 ELSE 1 END,
                last_fetch_time ASC
            LIMIT :limit
            """
            
            results = self.db.query(sql, {
                "status": NewsSourceStatus.ACTIVE.value,
                "limit": max_sources
            })
            
            if results:
                return [dict_to_news_source(row) for row in results]
            return []
            
        except Exception as e:
            logger.error(f"获取待更新新闻源失败: {e}")
            return []
    
    async def get_news_source_stats(self) -> Dict[str, Any]:
        """
        获取新闻源统计信息
        
        Returns:
            统计信息字典
        """
        try:
            stats = {}
            
            # 按状态统计
            sql_status = """
            SELECT status, COUNT(*) as count 
            FROM news_sources 
            GROUP BY status
            """
            status_results = self.db.query(sql_status)
            stats['by_status'] = {row['status']: row['count'] for row in status_results} if status_results else {}
            
            # 按类型统计
            sql_type = """
            SELECT source_type, COUNT(*) as count 
            FROM news_sources 
            GROUP BY source_type
            """
            type_results = self.db.query(sql_type)
            stats['by_type'] = {row['source_type']: row['count'] for row in type_results} if type_results else {}
            
            # 总文章数统计
            sql_total = "SELECT SUM(total_articles_fetched) as total FROM news_sources"
            total_result = self.db.query_one(sql_total)
            stats['total_articles_fetched'] = total_result['total'] if total_result and total_result['total'] else 0
            
            return stats
            
        except Exception as e:
            logger.error(f"获取新闻源统计信息失败: {e}")
            return {} 