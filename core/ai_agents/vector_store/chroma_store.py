#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ChromaDB向量存储实现
用于新闻语义相似性分析和检索
"""

import asyncio
import json
import logging
import os
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import hashlib

import chromadb
from chromadb.config import Settings

# 尝试导入sentence_transformers，如果失败则使用mock
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("sentence_transformers不可用，使用简单文本处理替代")
    
    class MockSentenceTransformer:
        """Mock SentenceTransformer for testing"""
        def __init__(self, model_name):
            self.model_name = model_name
            
        def encode(self, text):
            """简单的文本向量化mock实现"""
            import numpy as np
            # 使用文本长度和字符ASCII值的简单组合作为向量
            if isinstance(text, str):
                # 创建一个384维的向量（模拟all-MiniLM-L6-v2的输出维度）
                vector = np.zeros(384)
                for i, char in enumerate(text[:384]):
                    vector[i] = ord(char) / 255.0  # 归一化到0-1
                # 添加文本长度信息
                vector[0] = min(len(text) / 1000.0, 1.0)
                return vector
            return np.zeros(384)
    
    SentenceTransformer = MockSentenceTransformer

import numpy as np

# 配置日志
logger = logging.getLogger(__name__)

class ChromaNewsStore:
    """
    基于ChromaDB的新闻向量存储
    提供新闻文本的向量化存储和相似性检索
    """
    
    def __init__(self, 
                 db_path: Optional[str] = None,
                 embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
                 collection_name: str = "news_articles"):
        """
        初始化ChromaDB向量存储
        
        Args:
            db_path: 数据库存储路径
            embedding_model: 文本嵌入模型名称
            collection_name: 集合名称
        """
        self.db_path = db_path or os.getenv('CHROMA_DB_PATH', './data/chroma_db')
        self.embedding_model_name = embedding_model
        self.collection_name = collection_name
        
        # 确保存储目录存在
        os.makedirs(self.db_path, exist_ok=True)
        
        # 初始化ChromaDB客户端
        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # 初始化文本嵌入模型
        self.embedding_model = None
        self._initialize_embedding_model()
        
        # 获取或创建集合
        self.collection = self._get_or_create_collection()
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.info(f"ChromaDB初始化完成: 路径={self.db_path}, 模型={self.embedding_model_name}")
        else:
            logger.info(f"ChromaDB初始化完成(Mock模式): 路径={self.db_path}")
    
    def _initialize_embedding_model(self):
        """初始化文本嵌入模型"""
        try:
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                logger.info(f"加载嵌入模型: {self.embedding_model_name}")
            else:
                logger.info(f"使用Mock嵌入模型: {self.embedding_model_name}")
            
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            logger.info("嵌入模型加载成功")
        except Exception as e:
            logger.error(f"嵌入模型加载失败: {e}")
            raise
    
    def _get_or_create_collection(self):
        """获取或创建ChromaDB集合"""
        try:
            # 尝试获取现有集合
            collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"使用现有集合: {self.collection_name}")
        except ValueError:
            # 集合不存在，创建新集合
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "新闻文章向量存储"}
            )
            logger.info(f"创建新集合: {self.collection_name}")
        
        return collection
    
    def _generate_document_id(self, content: str, source: str = "") -> str:
        """生成文档唯一ID"""
        content_hash = hashlib.md5((content + source).encode()).hexdigest()
        return f"news_{content_hash}"
    
    def _preprocess_text(self, text: str) -> str:
        """预处理文本内容"""
        if not text:
            return ""
        
        # 移除多余空白字符
        text = ' '.join(text.split())
        
        # 限制文本长度（避免嵌入模型处理过长文本）
        max_length = 1000
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        return text
    
    async def add_news_article(self, 
                              article_id: int,
                              title: str,
                              content: str,
                              source: str = "",
                              metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        添加新闻文章到向量存储
        
        Args:
            article_id: 文章ID
            title: 文章标题
            content: 文章内容
            source: 新闻源
            metadata: 额外元数据
            
        Returns:
            bool: 是否添加成功
        """
        try:
            # 组合标题和内容用于向量化
            full_text = f"{title}\n{content}"
            processed_text = self._preprocess_text(full_text)
            
            if not processed_text:
                logger.warning(f"文章内容为空，跳过: article_id={article_id}")
                return False
            
            # 生成文档ID
            document_id = self._generate_document_id(processed_text, source)
            
            # 检查是否已存在
            try:
                existing = self.collection.get(ids=[document_id])
                if existing['ids']:
                    logger.info(f"文章已存在，跳过: document_id={document_id}")
                    return True
            except Exception:
                pass  # 文档不存在，继续添加
            
            # 生成文本嵌入
            logger.debug(f"生成文本嵌入: article_id={article_id}")
            embedding = await self._generate_embedding(processed_text)
            
            # 准备元数据
            doc_metadata = {
                "article_id": article_id,
                "title": title,
                "source": source,
                "created_at": datetime.now().isoformat(),
                "text_length": len(processed_text)
            }
            
            if metadata:
                doc_metadata.update(metadata)
            
            # 添加到集合
            self.collection.add(
                ids=[document_id],
                embeddings=[embedding.tolist()],
                documents=[processed_text],
                metadatas=[doc_metadata]
            )
            
            logger.info(f"新闻文章添加成功: article_id={article_id}, document_id={document_id}")
            return True
            
        except Exception as e:
            logger.error(f"添加新闻文章失败: article_id={article_id}, error={e}")
            return False
    
    async def _generate_embedding(self, text: str) -> np.ndarray:
        """生成文本嵌入向量"""
        try:
            # 在异步环境中运行同步的嵌入生成
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, 
                self.embedding_model.encode, 
                text
            )
            return embedding
        except Exception as e:
            logger.error(f"生成嵌入向量失败: {e}")
            raise
    
    async def search_similar_articles(self, 
                                     query_text: str,
                                     limit: int = 10,
                                     similarity_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        搜索相似新闻文章
        
        Args:
            query_text: 查询文本
            limit: 返回结果数量限制
            similarity_threshold: 相似度阈值
            
        Returns:
            List[Dict]: 相似文章列表，包含文章信息和相似度分数
        """
        try:
            if not query_text.strip():
                return []
            
            # 预处理查询文本
            processed_query = self._preprocess_text(query_text)
            
            # 生成查询嵌入
            logger.debug(f"生成查询嵌入: query={processed_query[:100]}...")
            query_embedding = await self._generate_embedding(processed_query)
            
            # 执行相似性搜索
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=limit
            )
            
            # 处理搜索结果
            similar_articles = []
            if results['ids'] and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    distance = results['distances'][0][i] if results['distances'] else 0
                    similarity = 1 - distance  # 转换为相似度分数
                    
                    # 过滤低相似度结果
                    if similarity < similarity_threshold:
                        continue
                    
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    document = results['documents'][0][i] if results['documents'] else ""
                    
                    similar_articles.append({
                        "document_id": doc_id,
                        "article_id": metadata.get("article_id"),
                        "title": metadata.get("title", ""),
                        "source": metadata.get("source", ""),
                        "similarity_score": round(similarity, 4),
                        "text_preview": document[:200] + "..." if len(document) > 200 else document,
                        "metadata": metadata
                    })
            
            logger.info(f"相似性搜索完成: 查询={processed_query[:50]}..., 结果数={len(similar_articles)}")
            return similar_articles
            
        except Exception as e:
            logger.error(f"相似性搜索失败: {e}")
            return []
    
    async def search_by_keywords(self, 
                                keywords: List[str],
                                limit: int = 10) -> List[Dict[str, Any]]:
        """
        基于关键词搜索相关文章
        
        Args:
            keywords: 关键词列表
            limit: 返回结果数量限制
            
        Returns:
            List[Dict]: 相关文章列表
        """
        if not keywords:
            return []
        
        # 将关键词组合为查询文本
        query_text = " ".join(keywords)
        return await self.search_similar_articles(query_text, limit)
    
    async def get_article_by_id(self, article_id: int) -> Optional[Dict[str, Any]]:
        """
        根据文章ID获取向量存储中的文章信息
        
        Args:
            article_id: 文章ID
            
        Returns:
            Optional[Dict]: 文章信息
        """
        try:
            # 搜索包含该article_id的文档
            results = self.collection.get(
                where={"article_id": article_id}
            )
            
            if results['ids']:
                doc_id = results['ids'][0]
                metadata = results['metadatas'][0] if results['metadatas'] else {}
                document = results['documents'][0] if results['documents'] else ""
                
                return {
                    "document_id": doc_id,
                    "article_id": article_id,
                    "title": metadata.get("title", ""),
                    "source": metadata.get("source", ""),
                    "content": document,
                    "metadata": metadata
                }
            
            return None
            
        except Exception as e:
            logger.error(f"获取文章失败: article_id={article_id}, error={e}")
            return None
    
    async def delete_article(self, article_id: int) -> bool:
        """
        删除文章
        
        Args:
            article_id: 文章ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            # 查找要删除的文档
            results = self.collection.get(
                where={"article_id": article_id}
            )
            
            if results['ids']:
                # 删除找到的文档
                self.collection.delete(ids=results['ids'])
                logger.info(f"文章删除成功: article_id={article_id}")
                return True
            else:
                logger.warning(f"文章不存在: article_id={article_id}")
                return False
                
        except Exception as e:
            logger.error(f"删除文章失败: article_id={article_id}, error={e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "db_path": self.db_path,
                "embedding_model": self.embedding_model_name,
                "status": "healthy"
            }
        except Exception as e:
            logger.error(f"获取集合统计失败: {e}")
            return {
                "collection_name": self.collection_name,
                "document_count": 0,
                "db_path": self.db_path,
                "embedding_model": self.embedding_model_name,
                "status": "error",
                "error_message": str(e)
            }
    
    async def batch_add_articles(self, 
                                articles: List[Dict[str, Any]],
                                batch_size: int = 50) -> Dict[str, int]:
        """
        批量添加文章
        
        Args:
            articles: 文章列表，每个包含 {id, title, content, source, metadata}
            batch_size: 批次大小
            
        Returns:
            Dict: 添加结果统计
        """
        total = len(articles)
        success_count = 0
        failed_count = 0
        
        logger.info(f"开始批量添加文章: 总数={total}, 批次大小={batch_size}")
        
        for i in range(0, total, batch_size):
            batch = articles[i:i + batch_size]
            logger.info(f"处理批次: {i // batch_size + 1}, 文章数={len(batch)}")
            
            for article in batch:
                try:
                    success = await self.add_news_article(
                        article_id=article.get('id'),
                        title=article.get('title', ''),
                        content=article.get('content', ''),
                        source=article.get('source', ''),
                        metadata=article.get('metadata', {})
                    )
                    
                    if success:
                        success_count += 1
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    logger.error(f"批量添加文章失败: article_id={article.get('id')}, error={e}")
                    failed_count += 1
        
        result = {
            "total": total,
            "success": success_count,
            "failed": failed_count,
            "success_rate": round(success_count / total * 100, 2) if total > 0 else 0
        }
        
        logger.info(f"批量添加完成: {result}")
        return result
    
    def reset_collection(self):
        """重置集合（删除所有数据）"""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self._get_or_create_collection()
            logger.info(f"集合重置完成: {self.collection_name}")
        except Exception as e:
            logger.error(f"重置集合失败: {e}")
            raise

# 全局实例
_global_chroma_store: Optional[ChromaNewsStore] = None

def get_chroma_store() -> ChromaNewsStore:
    """获取全局ChromaDB存储实例"""
    global _global_chroma_store
    if _global_chroma_store is None:
        _global_chroma_store = ChromaNewsStore()
    return _global_chroma_store 