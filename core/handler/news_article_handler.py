#!/usr/bin/env python3

"""
新闻文章处理器
负责处理新闻文章相关的业务逻辑
"""

import logging
from typing import Any, Optional

from ..models.news_article import (
    ArticleStatus,
    NewsArticle,
    NewsArticleCreate,
    NewsArticleUpdate,
)
from ..repository.news_article_repository import NewsArticleRepository

logger = logging.getLogger(__name__)


class NewsArticleHandler:
    """新闻文章处理器"""

    def __init__(self):
        """
        初始化新闻文章处理器
        """
        self.repository = NewsArticleRepository()

    async def create_news_article(
        self, article_data: dict[str, Any]
    ) -> Optional[NewsArticle]:
        """
        创建新闻文章

        Args:
            article_data: 新闻文章数据字典

        Returns:
            创建成功的新闻文章模型，失败返回None
        """
        try:
            # 验证必要字段
            required_fields = ["title", "url", "source_id"]
            for field in required_fields:
                if field not in article_data or not article_data[field]:
                    logger.error(f"缺少必要字段: {field}")
                    return None

            # 创建新闻文章模型
            article_create = NewsArticleCreate(**article_data)

            # 保存到数据库
            result = await self.repository.create_news_article(article_create)

            if result:
                logger.info(f"成功创建新闻文章: {result.title[:50]}... (ID: {result.id})")
            else:
                logger.error(f"创建新闻文章失败: {article_data.get('title', '')[:50]}...")

            return result

        except Exception as e:
            logger.error(f"创建新闻文章异常: {e}")
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
            return await self.repository.get_article_by_id(article_id)
        except Exception as e:
            logger.error(f"获取新闻文章失败 (ID: {article_id}): {e}")
            return None

    async def get_articles_by_source(
        self, source_id: int, limit: int = 50, offset: int = 0
    ) -> list[NewsArticle]:
        """
        根据新闻源获取文章列表

        Args:
            source_id: 新闻源ID
            limit: 限制返回数量
            offset: 偏移量

        Returns:
            新闻文章列表
        """
        try:
            return await self.repository.get_articles_by_source_id(
                source_id, limit, offset
            )
        except Exception as e:
            logger.error(f"获取新闻源文章失败 (源ID: {source_id}): {e}")
            return []

    async def get_recent_articles(
        self, hours: int = 24, limit: int = 100
    ) -> list[NewsArticle]:
        """
        获取最近的新闻文章

        Args:
            hours: 最近多少小时内的文章
            limit: 限制返回数量

        Returns:
            新闻文章列表
        """
        try:
            articles = await self.repository.get_recent_articles(hours, limit)
            logger.info(f"获取到 {len(articles)} 篇最近 {hours} 小时的文章")
            return articles
        except Exception as e:
            logger.error(f"获取最近新闻文章失败: {e}")
            return []

    async def get_pending_articles(self, limit: int = 100) -> list[NewsArticle]:
        """
        获取待处理的新闻文章

        Args:
            limit: 限制返回数量

        Returns:
            待处理的新闻文章列表
        """
        try:
            articles = await self.repository.get_articles_by_status(
                ArticleStatus.PENDING, limit
            )
            logger.info(f"找到 {len(articles)} 篇待处理文章")
            return articles
        except Exception as e:
            logger.error(f"获取待处理文章失败: {e}")
            return []

    async def search_articles(
        self, query: str, limit: int = 50, offset: int = 0
    ) -> list[NewsArticle]:
        """
        搜索新闻文章

        Args:
            query: 搜索关键词
            limit: 限制返回数量
            offset: 偏移量

        Returns:
            搜索结果文章列表
        """
        try:
            articles = await self.repository.search_articles(query, limit, offset)
            logger.info(f"搜索 '{query}' 找到 {len(articles)} 篇文章")
            return articles
        except Exception as e:
            logger.error(f"搜索新闻文章失败: {e}")
            return []

    async def update_article(
        self, article_id: int, update_data: dict[str, Any]
    ) -> Optional[NewsArticle]:
        """
        更新新闻文章

        Args:
            article_id: 新闻文章ID
            update_data: 更新数据字典

        Returns:
            更新后的新闻文章模型，失败返回None
        """
        try:
            # 过滤掉None值
            filtered_data = {k: v for k, v in update_data.items() if v is not None}

            if not filtered_data:
                logger.warning("没有提供有效的更新数据")
                return await self.repository.get_article_by_id(article_id)

            # 创建更新模型
            article_update = NewsArticleUpdate(**filtered_data)

            # 执行更新
            result = await self.repository.update_news_article(
                article_id, article_update
            )

            if result:
                logger.info(f"成功更新新闻文章 (ID: {article_id})")
            else:
                logger.error(f"更新新闻文章失败 (ID: {article_id})")

            return result

        except Exception as e:
            logger.error(f"更新新闻文章异常 (ID: {article_id}): {e}")
            return None

    async def mark_article_as_processing(self, article_id: int) -> bool:
        """
        标记文章为处理中状态

        Args:
            article_id: 文章ID

        Returns:
            更新是否成功
        """
        try:
            result = await self.repository.update_article_processing_status(
                article_id, ArticleStatus.PROCESSING
            )
            if result:
                logger.info(f"标记文章为处理中 (ID: {article_id})")
            return result
        except Exception as e:
            logger.error(f"标记文章处理状态异常 (ID: {article_id}): {e}")
            return False

    async def mark_article_as_processed(self, article_id: int) -> bool:
        """
        标记文章为已处理状态

        Args:
            article_id: 文章ID

        Returns:
            更新是否成功
        """
        try:
            result = await self.repository.update_article_processing_status(
                article_id, ArticleStatus.PROCESSED
            )
            if result:
                logger.info(f"标记文章为已处理 (ID: {article_id})")
            return result
        except Exception as e:
            logger.error(f"标记文章处理状态异常 (ID: {article_id}): {e}")
            return False

    async def mark_article_as_failed(self, article_id: int, error_message: str) -> bool:
        """
        标记文章为处理失败状态

        Args:
            article_id: 文章ID
            error_message: 错误信息

        Returns:
            更新是否成功
        """
        try:
            result = await self.repository.update_article_processing_status(
                article_id, ArticleStatus.FAILED, error_message
            )
            if result:
                logger.warning(f"标记文章为处理失败 (ID: {article_id}): {error_message}")
            return result
        except Exception as e:
            logger.error(f"标记文章处理状态异常 (ID: {article_id}): {e}")
            return False

    async def batch_create_articles(
        self, articles_data: list[dict[str, Any]]
    ) -> list[NewsArticle]:
        """
        批量创建新闻文章

        Args:
            articles_data: 新闻文章数据列表

        Returns:
            成功创建的新闻文章列表
        """
        try:
            # 转换为创建模型列表
            create_models = []
            for article_data in articles_data:
                try:
                    # 验证必要字段
                    required_fields = ["title", "url", "source_id"]
                    if all(
                        field in article_data and article_data[field]
                        for field in required_fields
                    ):
                        create_models.append(NewsArticleCreate(**article_data))
                    else:
                        logger.warning(
                            f"跳过无效文章数据: {article_data.get('title', 'Unknown')}"
                        )
                except Exception as e:
                    logger.error(f"转换文章数据失败: {e}")
                    continue

            # 批量创建
            created_articles = await self.repository.batch_create_articles(
                create_models
            )

            logger.info(f"批量创建完成，成功创建 {len(created_articles)}/{len(articles_data)} 篇文章")
            return created_articles

        except Exception as e:
            logger.error(f"批量创建文章异常: {e}")
            return []

    async def update_article_nlp_results(
        self, article_id: int, nlp_results: dict[str, Any]
    ) -> bool:
        """
        更新文章的NLP处理结果

        Args:
            article_id: 文章ID
            nlp_results: NLP处理结果，包含entities, keywords, sentiment_score, topics等

        Returns:
            更新是否成功
        """
        try:
            # 准备更新数据
            update_data = {}

            # 实体识别结果
            if "entities" in nlp_results:
                update_data["entities"] = nlp_results["entities"]

            # 关键词提取结果
            if "keywords" in nlp_results:
                update_data["keywords"] = nlp_results["keywords"]

            # 情感分析得分
            if "sentiment_score" in nlp_results:
                update_data["sentiment_score"] = nlp_results["sentiment_score"]

            # 主题分析结果
            if "topics" in nlp_results:
                update_data["topics"] = nlp_results["topics"]

            # 重要性评分
            if "importance_score" in nlp_results:
                update_data["importance_score"] = nlp_results["importance_score"]

            # 市场相关性评分
            if "market_relevance_score" in nlp_results:
                update_data["market_relevance_score"] = nlp_results[
                    "market_relevance_score"
                ]

            # 字数统计
            if "word_count" in nlp_results:
                update_data["word_count"] = nlp_results["word_count"]

            # 阅读时间
            if "read_time_minutes" in nlp_results:
                update_data["read_time_minutes"] = nlp_results["read_time_minutes"]

            # 执行更新
            result = await self.update_article(article_id, update_data)

            success = result is not None
            if success:
                logger.info(f"成功更新文章NLP结果 (ID: {article_id})")
            else:
                logger.error(f"更新文章NLP结果失败 (ID: {article_id})")

            return success

        except Exception as e:
            logger.error(f"更新文章NLP结果异常 (ID: {article_id}): {e}")
            return False

    async def get_high_importance_articles(
        self, min_score: float = 0.7, limit: int = 50
    ) -> list[NewsArticle]:
        """
        获取高重要性的新闻文章

        Args:
            min_score: 最小重要性评分
            limit: 限制返回数量

        Returns:
            高重要性新闻文章列表
        """
        try:
            # 这里可以通过repository添加专门的查询方法
            # 暂时使用搜索功能模拟
            recent_articles = await self.get_recent_articles(24, 200)

            # 过滤高重要性文章
            high_importance = [
                article
                for article in recent_articles
                if article.importance_score >= min_score
            ]

            # 按重要性排序并限制数量
            high_importance.sort(key=lambda x: x.importance_score, reverse=True)
            result = high_importance[:limit]

            logger.info(f"找到 {len(result)} 篇高重要性文章 (评分 >= {min_score})")
            return result

        except Exception as e:
            logger.error(f"获取高重要性文章失败: {e}")
            return []

    async def clean_old_articles(self, days: int = 30) -> dict[str, Any]:
        """
        清理旧文章

        Args:
            days: 保留天数

        Returns:
            清理结果统计
        """
        try:
            deleted_count = await self.repository.delete_old_articles(days)

            result = {
                "deleted_count": deleted_count,
                "retention_days": days,
                "status": "success",
            }

            logger.info(f"清理旧文章完成，删除了 {deleted_count} 篇超过 {days} 天的文章")
            return result

        except Exception as e:
            logger.error(f"清理旧文章失败: {e}")
            return {
                "deleted_count": 0,
                "retention_days": days,
                "status": "failed",
                "error": str(e),
            }

    async def get_article_stats(self) -> dict[str, Any]:
        """
        获取新闻文章统计信息

        Returns:
            统计信息字典
        """
        try:
            stats = await self.repository.get_article_stats()
            logger.info("成功获取新闻文章统计信息")
            return stats
        except Exception as e:
            logger.error(f"获取新闻文章统计信息失败: {e}")
            return {}

    async def validate_article_data(
        self, article_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        验证新闻文章数据

        Args:
            article_data: 文章数据

        Returns:
            验证结果字典，包含 is_valid 和 errors 字段
        """
        try:
            errors = []

            # 检查必要字段
            required_fields = ["title", "url", "source_id"]
            for field in required_fields:
                if field not in article_data or not article_data[field]:
                    errors.append(f"缺少必要字段: {field}")

            # 检查标题长度
            if "title" in article_data and article_data["title"]:
                if len(article_data["title"]) > 1024:
                    errors.append("标题长度不能超过1024个字符")

            # 检查URL格式
            if "url" in article_data and article_data["url"]:
                url = article_data["url"]
                if not url.startswith(("http://", "https://")):
                    errors.append("URL必须以http://或https://开头")
                if len(url) > 2048:
                    errors.append("URL长度不能超过2048个字符")

            # 检查source_id
            if "source_id" in article_data:
                try:
                    source_id = int(article_data["source_id"])
                    if source_id <= 0:
                        errors.append("source_id必须是正整数")
                except (ValueError, TypeError):
                    errors.append("source_id必须是有效的整数")

            # 检查情感分析得分
            if (
                "sentiment_score" in article_data
                and article_data["sentiment_score"] is not None
            ):
                try:
                    score = float(article_data["sentiment_score"])
                    if not -1.0 <= score <= 1.0:
                        errors.append("情感分析得分必须在-1.0到1.0之间")
                except (ValueError, TypeError):
                    errors.append("情感分析得分必须是有效的浮点数")

            return {"is_valid": len(errors) == 0, "errors": errors}

        except Exception as e:
            logger.error(f"验证文章数据异常: {e}")
            return {"is_valid": False, "errors": [f"验证过程出错: {str(e)}"]}
