#!/usr/bin/env python3

"""
新闻源处理器
负责处理新闻源相关的业务逻辑
"""

import logging
from typing import Any, Optional

from ..models.news_source import (
    NewsSource,
    NewsSourceCreate,
    NewsSourceStatus,
    NewsSourceType,
    NewsSourceUpdate,
)
from ..service.news_source_repository import NewsSourceRepository

logger = logging.getLogger(__name__)


class NewsSourceHandler:
    """新闻源处理器"""

    def __init__(self):
        """
        初始化新闻源处理器
        """
        self.repository = NewsSourceRepository()

    async def create_news_source(
        self, source_data: dict[str, Any]
    ) -> Optional[NewsSource]:
        """
        创建新闻源

        Args:
            source_data: 新闻源数据字典

        Returns:
            创建成功的新闻源模型，失败返回None
        """
        try:
            # 验证必要字段
            required_fields = ["name", "source_type", "url"]
            for field in required_fields:
                if field not in source_data or not source_data[field]:
                    logger.error(f"缺少必要字段: {field}")
                    return None

            # 创建新闻源模型
            source_create = NewsSourceCreate(**source_data)

            # 保存到数据库
            result = await self.repository.create_news_source(source_create)

            if result:
                logger.info(f"成功创建新闻源: {result.name} (ID: {result.id})")
            else:
                logger.error(f"创建新闻源失败: {source_data.get('name')}")

            return result

        except Exception as e:
            logger.error(f"创建新闻源异常: {e}")
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
            return await self.repository.get_news_source_by_id(source_id)
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
            return await self.repository.get_news_source_by_name(name)
        except Exception as e:
            logger.error(f"获取新闻源失败 (名称: {name}): {e}")
            return None

    async def get_all_news_sources(
        self, limit: int = 100, offset: int = 0
    ) -> list[NewsSource]:
        """
        获取所有新闻源

        Args:
            limit: 限制返回数量
            offset: 偏移量

        Returns:
            新闻源列表
        """
        try:
            return await self.repository.get_all_news_sources(limit, offset)
        except Exception as e:
            logger.error(f"获取所有新闻源失败: {e}")
            return []

    async def get_active_news_sources(self) -> list[NewsSource]:
        """
        获取所有活跃的新闻源

        Returns:
            活跃的新闻源列表
        """
        try:
            return await self.repository.get_news_sources_by_status(
                NewsSourceStatus.ACTIVE
            )
        except Exception as e:
            logger.error(f"获取活跃新闻源失败: {e}")
            return []

    async def update_news_source(
        self, source_id: int, update_data: dict[str, Any]
    ) -> Optional[NewsSource]:
        """
        更新新闻源

        Args:
            source_id: 新闻源ID
            update_data: 更新数据字典

        Returns:
            更新后的新闻源模型，失败返回None
        """
        try:
            # 过滤掉None值
            filtered_data = {k: v for k, v in update_data.items() if v is not None}

            if not filtered_data:
                logger.warning("没有提供有效的更新数据")
                return await self.repository.get_news_source_by_id(source_id)

            # 创建更新模型
            source_update = NewsSourceUpdate(**filtered_data)

            # 执行更新
            result = await self.repository.update_news_source(source_id, source_update)

            if result:
                logger.info(f"成功更新新闻源: {result.name} (ID: {source_id})")
            else:
                logger.error(f"更新新闻源失败 (ID: {source_id})")

            return result

        except Exception as e:
            logger.error(f"更新新闻源异常 (ID: {source_id}): {e}")
            return None

    async def delete_news_source(self, source_id: int) -> bool:
        """
        删除新闻源

        Args:
            source_id: 新闻源ID

        Returns:
            删除是否成功
        """
        try:
            # 先检查新闻源是否存在
            source = await self.repository.get_news_source_by_id(source_id)
            if not source:
                logger.warning(f"新闻源不存在 (ID: {source_id})")
                return False

            # 执行删除
            result = await self.repository.delete_news_source(source_id)

            if result:
                logger.info(f"成功删除新闻源: {source.name} (ID: {source_id})")
            else:
                logger.error(f"删除新闻源失败 (ID: {source_id})")

            return result

        except Exception as e:
            logger.error(f"删除新闻源异常 (ID: {source_id}): {e}")
            return False

    async def toggle_news_source_status(self, source_id: int) -> Optional[NewsSource]:
        """
        切换新闻源状态（活跃/非活跃）

        Args:
            source_id: 新闻源ID

        Returns:
            更新后的新闻源模型，失败返回None
        """
        try:
            # 获取当前新闻源
            source = await self.repository.get_news_source_by_id(source_id)
            if not source:
                logger.warning(f"新闻源不存在 (ID: {source_id})")
                return None

            # 切换状态
            new_status = (
                NewsSourceStatus.INACTIVE
                if source.status == NewsSourceStatus.ACTIVE
                else NewsSourceStatus.ACTIVE
            )

            # 更新状态
            result = await self.update_news_source(source_id, {"status": new_status})

            if result:
                logger.info(f"成功切换新闻源状态: {source.name} -> {new_status.value}")

            return result

        except Exception as e:
            logger.error(f"切换新闻源状态异常 (ID: {source_id}): {e}")
            return None

    async def update_source_fetch_result(
        self,
        source_id: int,
        success: bool,
        error_message: str = None,
        article_count: int = 0,
    ) -> bool:
        """
        更新新闻源抓取结果

        Args:
            source_id: 新闻源ID
            success: 抓取是否成功
            error_message: 错误信息（可选）
            article_count: 抓取的文章数量

        Returns:
            更新是否成功
        """
        try:
            if success:
                result = await self.repository.update_last_fetch_info(
                    source_id, None, article_count
                )
                logger.info(f"更新新闻源抓取成功信息 (ID: {source_id}, 文章数: {article_count})")
            else:
                result = await self.repository.update_last_fetch_info(
                    source_id, error_message, 0
                )
                logger.warning(f"更新新闻源抓取失败信息 (ID: {source_id}, 错误: {error_message})")

            return result

        except Exception as e:
            logger.error(f"更新新闻源抓取结果异常 (ID: {source_id}): {e}")
            return False

    async def get_sources_for_update(self, max_sources: int = 50) -> list[NewsSource]:
        """
        获取需要更新的新闻源

        Args:
            max_sources: 最大返回数量

        Returns:
            需要更新的新闻源列表
        """
        try:
            sources = await self.repository.get_sources_for_update(max_sources)
            logger.info(f"找到 {len(sources)} 个需要更新的新闻源")
            return sources

        except Exception as e:
            logger.error(f"获取待更新新闻源失败: {e}")
            return []

    async def get_news_source_stats(self) -> dict[str, Any]:
        """
        获取新闻源统计信息

        Returns:
            统计信息字典
        """
        try:
            stats = await self.repository.get_news_source_stats()
            logger.info("成功获取新闻源统计信息")
            return stats

        except Exception as e:
            logger.error(f"获取新闻源统计信息失败: {e}")
            return {}

    async def batch_create_news_sources(
        self, sources_data: list[dict[str, Any]]
    ) -> list[NewsSource]:
        """
        批量创建新闻源

        Args:
            sources_data: 新闻源数据列表

        Returns:
            成功创建的新闻源列表
        """
        created_sources = []

        for source_data in sources_data:
            try:
                created = await self.create_news_source(source_data)
                if created:
                    created_sources.append(created)
            except Exception as e:
                logger.error(f"批量创建新闻源失败: {e}")
                continue

        logger.info(f"批量创建完成，成功创建 {len(created_sources)}/{len(sources_data)} 个新闻源")
        return created_sources

    async def validate_news_source_config(
        self, source_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        验证新闻源配置

        Args:
            source_data: 新闻源数据

        Returns:
            验证结果字典，包含 is_valid 和 errors 字段
        """
        try:
            errors = []

            # 检查必要字段
            required_fields = ["name", "source_type", "url"]
            for field in required_fields:
                if field not in source_data or not source_data[field]:
                    errors.append(f"缺少必要字段: {field}")

            # 检查源类型
            if "source_type" in source_data:
                valid_types = [t.value for t in NewsSourceType]
                if source_data["source_type"] not in valid_types:
                    errors.append(f"无效的源类型: {source_data['source_type']}")

            # 检查URL格式
            if "url" in source_data and source_data["url"]:
                url = source_data["url"]
                if not url.startswith(("http://", "https://")):
                    errors.append("URL必须以http://或https://开头")

            # 检查更新频率
            if "update_frequency" in source_data:
                freq = source_data["update_frequency"]
                if not isinstance(freq, int) or freq < 300:  # 最少5分钟
                    errors.append("更新频率必须是大于等于300秒的整数")

            # 检查最大文章数
            if "max_articles_per_fetch" in source_data:
                max_articles = source_data["max_articles_per_fetch"]
                if (
                    not isinstance(max_articles, int)
                    or max_articles < 1
                    or max_articles > 200
                ):
                    errors.append("每次抓取最大文章数必须在1-200之间")

            return {"is_valid": len(errors) == 0, "errors": errors}

        except Exception as e:
            logger.error(f"验证新闻源配置异常: {e}")
            return {"is_valid": False, "errors": [f"验证过程出错: {str(e)}"]}
