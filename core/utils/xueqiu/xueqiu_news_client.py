"""
雪球新闻聚合客户端
专门处理雪球平台的投资动态和新闻数据
"""

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional

from ...models.news_article import ArticleStatus
from ...models.news_source import NewsSource
from .xueqiu_base_client import XueqiuBaseClient

logger = logging.getLogger(__name__)


class XueqiuNewsClient(XueqiuBaseClient):
    """雪球新闻聚合客户端"""

    def get_client_type(self) -> str:
        """返回客户端类型"""
        return "news"

    async def fetch_timeline_data(
        self, news_source: NewsSource
    ) -> list[dict[str, Any]]:
        """
        抓取雪球时间线数据

        Args:
            news_source: 新闻源配置

        Returns:
            新闻文章列表
        """
        try:
            logger.info(f"开始抓取雪球数据: {news_source.name}")

            # 首先初始化会话（获取必要的cookie和token）
            await self._init_session()

            # 抓取时间线数据
            timeline_data = await self._fetch_timeline_api(news_source.url)
            if not timeline_data:
                raise ValueError("无法获取雪球时间线数据")

            # 解析数据
            articles = []
            max_articles = news_source.max_articles_per_fetch or 20

            items = timeline_data.get("list", [])[:max_articles]

            for item in items:
                try:
                    article_data = await self._parse_timeline_item(item, news_source)
                    if article_data and self._should_include_article(
                        article_data, news_source
                    ):
                        articles.append(article_data)
                except Exception as e:
                    logger.error(f"解析雪球条目失败: {e}", exc_info=True)
                    continue

            logger.info(f"成功抓取 {len(articles)} 篇雪球动态")
            return articles

        except Exception as e:
            logger.error(f"抓取雪球数据失败 {news_source.name}: {e}", exc_info=True)
            raise

    async def _init_session(self):
        """初始化雪球会话"""
        try:
            # 访问雪球首页，获取必要的session信息
            async with self.session.get("https://xueqiu.com/") as response:
                if response.status == 200:
                    logger.debug("雪球会话初始化成功")
                else:
                    logger.warning(f"雪球会话初始化警告: {response.status}")
        except Exception as e:
            logger.warning(f"雪球会话初始化失败: {e}")

    async def _fetch_timeline_api(self, url: str) -> Optional[dict]:
        """获取时间线数据"""
        return await self._async_request(url)

    async def _parse_timeline_item(
        self, item: dict, news_source: NewsSource
    ) -> Optional[dict[str, Any]]:
        """
        解析雪球条目

        Args:
            item: 雪球API返回的条目
            news_source: 新闻源配置

        Returns:
            解析后的文章数据
        """
        try:
            # 基础信息提取
            title = self._extract_title(item)
            text = self._extract_text(item)

            if not title and not text:
                return None

            # 构建URL
            status_id = item.get("id", "")
            url = f"https://xueqiu.com/statuses/show/{status_id}" if status_id else ""

            # 生成URL哈希
            content_for_hash = f"{title}_{text}_{status_id}"
            url_hash = hashlib.sha256(content_for_hash.encode("utf-8")).hexdigest()

            # 时间处理
            published_at = self._parse_created_time(item)

            # 用户信息
            author = self._extract_author(item)

            # 股票相关性检测
            stock_symbols = self._extract_stock_symbols(text)
            category = "雪球动态"
            if stock_symbols:
                category = f"雪球股票-{','.join(stock_symbols[:3])}"

            # 计算重要性（基于转发、评论、点赞数）
            importance_score = self._calculate_importance(item)

            article_data = {
                "title": title or text[:50] + "...",  # 如果没有标题，用内容前50字符
                "url": url,
                "url_hash": url_hash,
                "content": text,
                "summary": text[:200] + "..." if len(text) > 200 else text,
                "author": author,
                "source_id": news_source.id,
                "source_name": news_source.name,
                "category": category,
                "published_at": published_at,
                "language": news_source.language,
                "region": news_source.region,
                "status": ArticleStatus.PENDING.value,
                "word_count": len(text) if text else 0,
                "importance_score": importance_score,
                "metadata": json.dumps(
                    {
                        "platform": "xueqiu",
                        "status_id": status_id,
                        "stock_symbols": stock_symbols,
                        "retweet_count": item.get("retweet_count", 0),
                        "reply_count": item.get("reply_count", 0),
                        "like_count": item.get("like_count", 0),
                    },
                    ensure_ascii=False,
                ),
            }

            return article_data

        except Exception as e:
            logger.error(f"解析雪球条目失败: {e}", exc_info=True)
            return None

    def _extract_title(self, item: dict) -> str:
        """提取标题"""
        try:
            # 尝试从不同字段提取标题
            title_candidates = [
                item.get("title", ""),
                item.get("text", ""),
                item.get("description", ""),
            ]

            for candidate in title_candidates:
                if candidate and isinstance(candidate, str):
                    # 清理HTML标签
                    import re

                    clean_title = re.sub(r"<[^>]+>", "", candidate)
                    if clean_title.strip():
                        # 取前50个字符作为标题
                        return clean_title.strip()[:50]

            return ""

        except Exception as e:
            logger.error(f"提取标题失败: {e}")
            return ""

    def _extract_text(self, item: dict) -> str:
        """提取正文内容"""
        try:
            text_candidates = [
                item.get("text", ""),
                item.get("description", ""),
                item.get("title", ""),
            ]

            for candidate in text_candidates:
                if candidate and isinstance(candidate, str):
                    # 清理HTML标签
                    import re

                    clean_text = re.sub(r"<[^>]+>", "", candidate)
                    if clean_text.strip():
                        return clean_text.strip()

            return ""

        except Exception as e:
            logger.error(f"提取正文失败: {e}")
            return ""

    def _parse_created_time(self, item: dict) -> Optional[datetime]:
        """解析创建时间"""
        try:
            created_at = item.get("created_at")
            if not created_at:
                return None

            # 雪球的时间戳通常是毫秒级
            if isinstance(created_at, (int, float)):
                # 如果是毫秒时间戳，转换为秒
                if created_at > 1e10:
                    created_at = created_at / 1000

                return datetime.fromtimestamp(created_at, tz=timezone.utc)

            return None

        except Exception as e:
            logger.error(f"解析时间失败: {e}")
            return None

    def _extract_author(self, item: dict) -> Optional[str]:
        """提取作者信息"""
        try:
            user = item.get("user", {})
            return user.get("screen_name") or user.get("name") or user.get("id")
        except BaseException:
            return None

    def _extract_stock_symbols(self, text: str) -> list[str]:
        """从文本中提取股票代码"""
        if not text:
            return []

        try:
            # 匹配股票代码模式
            patterns = [
                r"\$([A-Z]{2}\d{6})",  # $SH600000
                r"\$([A-Z]{1,5})",  # $AAPL
                r"([A-Z]{2}\d{6})",  # SH600000
                r"(\d{6})",  # 600000
            ]

            symbols = []
            for pattern in patterns:
                matches = re.findall(pattern, text)
                symbols.extend(matches)

            # 去重并返回
            return list(set(symbols))

        except Exception as e:
            logger.error(f"提取股票代码失败: {e}")
            return []

    def _calculate_importance(self, item: dict) -> float:
        """计算重要性评分"""
        try:
            # 基于互动数据计算重要性
            retweet_count = item.get("retweet_count", 0)
            reply_count = item.get("reply_count", 0)
            like_count = item.get("like_count", 0)

            # 权重设置
            retweet_weight = 3.0
            reply_weight = 2.0
            like_weight = 1.0

            # 计算总分
            total_score = (
                retweet_count * retweet_weight
                + reply_count * reply_weight
                + like_count * like_weight
            )

            # 归一化到0-1范围
            if total_score > 0:
                # 使用对数函数进行归一化，避免极值
                import math

                normalized_score = min(1.0, math.log10(total_score + 1) / 4.0)
                return round(normalized_score, 3)

            return 0.0

        except Exception as e:
            logger.error(f"计算重要性失败: {e}")
            return 0.0

    def _should_include_article(
        self, article_data: dict[str, Any], news_source: NewsSource
    ) -> bool:
        """判断是否应该包含这篇文章"""
        try:
            # 基本过滤条件
            if not article_data.get("content"):
                return False

            # 内容长度过滤
            content_length = len(article_data.get("content", ""))
            if content_length < 10:  # 内容太短
                return False

            if content_length > 10000:  # 内容太长，可能是异常数据
                return False

            # 如果新闻源有关键词过滤器
            if hasattr(news_source, "keyword_filters") and news_source.keyword_filters:
                content = article_data.get("content", "").lower()
                for keyword in news_source.keyword_filters:
                    if keyword.lower() in content:
                        return True
                # 如果有关键词过滤器但都不匹配，排除
                return False

            return True

        except Exception as e:
            logger.error(f"文章过滤判断失败: {e}")
            return True  # 默认包含


# 兼容性函数，保持与原代码的兼容
async def fetch_xueqiu_data(news_source: NewsSource) -> list[dict[str, Any]]:
    """
    兼容性函数：抓取雪球数据

    Args:
        news_source: 新闻源配置

    Returns:
        新闻文章列表
    """
    async with XueqiuNewsClient() as client:
        return await client.fetch_timeline_data(news_source)
