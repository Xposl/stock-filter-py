#!/usr/bin/env python3

"""
API新闻聚合器
负责从API源抓取新闻数据，特别处理雪球、东方财富等平台
"""

import hashlib
import logging
import re
import ssl
from datetime import datetime, timezone
from typing import Any, Optional

import aiohttp

from ..models.news_article import ArticleStatus
from ..models.news_source import NewsSource

logger = logging.getLogger(__name__)


class APIAggregator:
    """API新闻聚合器"""

    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        """
        初始化API聚合器

        Args:
            session: 可选的aiohttp客户端会话
        """
        self.session = session
        self._own_session = session is None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        if self._own_session:
            # SSL配置
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            connector = aiohttp.TCPConnector(
                limit=100, limit_per_host=30, ssl=ssl_context
            )
            timeout = aiohttp.ClientTimeout(total=30, connect=10)

            # 配置常用的请求头
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }

            self.session = aiohttp.ClientSession(
                connector=connector, timeout=timeout, headers=headers
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self._own_session and self.session:
            await self.session.close()

    async def fetch_api_feed(self, news_source: NewsSource) -> list[dict[str, Any]]:
        """
        抓取API源

        Args:
            news_source: 新闻源配置

        Returns:
            新闻文章列表
        """
        try:
            logger.info(f"开始抓取API源: {news_source.name} ({news_source.url})")

            # 根据源名称选择抓取策略
            if "雪球" in news_source.name:
                return await self._fetch_xueqiu_feed(news_source)
            elif "东方财富" in news_source.name:
                return await self._fetch_eastmoney_feed(news_source)
            else:
                # 通用API抓取
                return await self._fetch_generic_api_feed(news_source)

        except Exception as e:
            logger.error(f"抓取API源失败 {news_source.name}: {e}", exc_info=True)
            raise

    async def _fetch_xueqiu_feed(self, news_source: NewsSource) -> list[dict[str, Any]]:
        """
        抓取雪球API数据

        Args:
            news_source: 雪球新闻源配置

        Returns:
            解析后的文章列表
        """
        try:
            if not self.session:
                raise ValueError("Session not initialized. Use async context manager.")

            articles = []

            # 设置雪球特定的请求头
            headers = {
                "Referer": "https://xueqiu.com/",
                "X-Requested-With": "XMLHttpRequest",
            }

            # 根据不同的雪球API构建请求
            if "热门话题" in news_source.name:
                # 热门话题API
                params = {"size": news_source.max_articles_per_fetch or 20, "page": 1}
                url = news_source.url

            elif "今日话题" in news_source.name:
                # 今日话题API
                params = {
                    "size": news_source.max_articles_per_fetch or 15,
                    "page": 1,
                    "category": -1,  # 全部分类
                }
                url = news_source.url
            else:
                # 默认处理
                params = {"size": news_source.max_articles_per_fetch or 20}
                url = news_source.url

            # 发起请求
            async with self.session.get(
                url, params=params, headers=headers
            ) as response:
                if response.status != 200:
                    raise ValueError(f"HTTP错误 {response.status}")

                data = await response.json()

                # 解析雪球API响应
                if "list" in data:
                    items = data["list"]
                elif "statuses" in data:
                    items = data["statuses"]
                else:
                    items = data if isinstance(data, list) else []

                for item in items:
                    try:
                        article_data = self._parse_xueqiu_item(item, news_source)
                        if article_data:
                            articles.append(article_data)
                    except Exception as e:
                        logger.error(f"解析雪球条目失败: {e}")
                        continue

            logger.info(f"成功抓取 {len(articles)} 篇雪球文章")
            return articles

        except Exception as e:
            logger.error(f"抓取雪球API源失败: {e}")
            raise

    async def _fetch_eastmoney_feed(
        self, news_source: NewsSource
    ) -> list[dict[str, Any]]:
        """
        抓取东方财富API数据

        Args:
            news_source: 东方财富新闻源配置

        Returns:
            解析后的文章列表
        """
        try:
            if not self.session:
                raise ValueError("Session not initialized. Use async context manager.")

            articles = []

            # 根据不同的东方财富API构建请求
            if "研报中心" in news_source.name:
                # 研报API
                params = {
                    "pagesize": news_source.max_articles_per_fetch or 10,
                    "page": 1,
                    "sortColumns": "REPORT_DATE",
                    "sortTypes": "-1",
                }
            else:
                # 股票资讯API
                params = {
                    "pagesize": news_source.max_articles_per_fetch or 20,
                    "page": 1,
                    "type": "stock",  # 股票类型
                }

            url = news_source.url

            # 发起请求
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    raise ValueError(f"HTTP错误 {response.status}")

                data = await response.json()

                # 解析东方财富API响应
                if "result" in data and "data" in data["result"]:
                    items = data["result"]["data"]
                elif "data" in data:
                    items = data["data"]
                else:
                    items = data if isinstance(data, list) else []

                for item in items:
                    try:
                        article_data = self._parse_eastmoney_item(item, news_source)
                        if article_data:
                            articles.append(article_data)
                    except Exception as e:
                        logger.error(f"解析东方财富条目失败: {e}")
                        continue

            logger.info(f"成功抓取 {len(articles)} 篇东方财富文章")
            return articles

        except Exception as e:
            logger.error(f"抓取东方财富API源失败: {e}")
            raise

    async def _fetch_generic_api_feed(
        self, news_source: NewsSource
    ) -> list[dict[str, Any]]:
        """
        通用API抓取

        Args:
            news_source: 新闻源配置

        Returns:
            解析后的文章列表
        """
        try:
            if not self.session:
                raise ValueError("Session not initialized. Use async context manager.")

            articles = []

            # 通用参数
            params = {"limit": news_source.max_articles_per_fetch or 20, "page": 1}

            async with self.session.get(news_source.url, params=params) as response:
                if response.status != 200:
                    raise ValueError(f"HTTP错误 {response.status}")

                data = await response.json()

                # 尝试解析常见的API响应格式
                if isinstance(data, dict):
                    # 尝试常见的数据字段
                    items = data.get(
                        "data",
                        data.get("items", data.get("list", data.get("articles", []))),
                    )
                else:
                    items = data if isinstance(data, list) else []

                for item in items:
                    try:
                        article_data = self._parse_generic_item(item, news_source)
                        if article_data:
                            articles.append(article_data)
                    except Exception as e:
                        logger.error(f"解析API条目失败: {e}")
                        continue

            logger.info(f"成功抓取 {len(articles)} 篇通用API文章")
            return articles

        except Exception as e:
            logger.error(f"抓取通用API源失败: {e}")
            raise

    def _parse_xueqiu_item(
        self, item: dict[str, Any], news_source: NewsSource
    ) -> Optional[dict[str, Any]]:
        """解析雪球条目"""
        try:
            # 提取基础信息
            title = item.get("title", item.get("description", ""))[:200]  # 限制标题长度
            if not title:
                return None

            # 构建URL（雪球的文章链接）
            status_id = item.get("id", item.get("status_id", ""))
            if status_id:
                url = f"https://xueqiu.com/{status_id}"
            else:
                url = f"https://xueqiu.com/statuses/{status_id}"

            # 生成URL哈希 (使用SHA256替代MD5)
            url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()

            # 提取内容
            content = item.get("text", item.get("description", ""))
            summary = content[:500] if content else title  # 前500字符作为摘要

            # 提取作者信息
            user_info = item.get("user", {})
            author = user_info.get("screen_name", user_info.get("name", ""))

            # 时间处理
            created_at = item.get("created_at", item.get("timestamp", 0))
            if isinstance(created_at, (int, float)):
                published_at = datetime.fromtimestamp(
                    created_at / 1000 if created_at > 1e10 else created_at,
                    tz=timezone.utc,
                )
            else:
                published_at = datetime.now(tz=timezone.utc)

            # 计算重要性评分（基于转发数、评论数等）
            retweet_count = item.get("retweet_count", 0)
            reply_count = item.get("reply_count", 0)
            fav_count = item.get("fav_count", 0)

            # 简单的重要性算法
            importance_score = min(
                1.0, (retweet_count * 0.3 + reply_count * 0.4 + fav_count * 0.3) / 100
            )

            article_data = {
                "title": self._clean_text(title),
                "url": url,
                "url_hash": url_hash,
                "content": self._clean_text(content),
                "summary": self._clean_text(summary),
                "author": author,
                "source_id": news_source.id,
                "source_name": news_source.name,
                "published_at": published_at,
                "language": news_source.language,
                "region": news_source.region,
                "status": ArticleStatus.PENDING.value,
                "importance_score": importance_score,
                "market_relevance_score": 0.8,  # 雪球内容通常与市场相关
                "word_count": len(content) if content else len(title),
            }

            return article_data

        except Exception as e:
            logger.error(f"解析雪球条目失败: {e}")
            return None

    def _parse_eastmoney_item(
        self, item: dict[str, Any], news_source: NewsSource
    ) -> Optional[dict[str, Any]]:
        """解析东方财富条目"""
        try:
            # 提取基础信息
            title = item.get("title", item.get("TITLE", item.get("name", "")))
            if not title:
                return None

            # URL处理
            url = item.get("url", item.get("URL", ""))
            if not url.startswith("http"):
                # 如果是相对URL，补充完整URL
                url = f"http://finance.eastmoney.com{url}"

            # 生成URL哈希 (使用SHA256替代MD5)
            url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()

            # 提取内容
            content = item.get("content", item.get("CONTENT", item.get("summary", "")))
            summary = content[:500] if content else title[:200]

            # 提取作者
            author = item.get("author", item.get("AUTHOR", ""))

            # 时间处理
            pub_time = item.get(
                "pub_time", item.get("REPORT_DATE", item.get("create_time", ""))
            )
            if pub_time:
                try:
                    if isinstance(pub_time, str):
                        published_at = datetime.fromisoformat(
                            pub_time.replace("Z", "+00:00")
                        )
                    else:
                        published_at = datetime.fromtimestamp(pub_time, tz=timezone.utc)
                except BaseException:
                    published_at = datetime.now(tz=timezone.utc)
            else:
                published_at = datetime.now(tz=timezone.utc)

            # 分类信息
            category = item.get("category", item.get("type", ""))

            article_data = {
                "title": self._clean_text(title),
                "url": url,
                "url_hash": url_hash,
                "content": self._clean_text(content),
                "summary": self._clean_text(summary),
                "author": author,
                "source_id": news_source.id,
                "source_name": news_source.name,
                "category": category,
                "published_at": published_at,
                "language": news_source.language,
                "region": news_source.region,
                "status": ArticleStatus.PENDING.value,
                "importance_score": 0.6,  # 东方财富内容基础重要性
                "market_relevance_score": 0.9,  # 高市场相关性
                "word_count": len(content) if content else len(title),
            }

            return article_data

        except Exception as e:
            logger.error(f"解析东方财富条目失败: {e}")
            return None

    def _parse_generic_item(
        self, item: dict[str, Any], news_source: NewsSource
    ) -> Optional[dict[str, Any]]:
        """解析通用API条目"""
        try:
            # 尝试多种可能的字段名
            title_fields = ["title", "name", "subject", "headline"]
            title = ""
            for field in title_fields:
                if field in item and item[field]:
                    title = str(item[field])
                    break

            if not title:
                return None

            # URL字段
            url_fields = ["url", "link", "href"]
            url = ""
            for field in url_fields:
                if field in item and item[field]:
                    url = str(item[field])
                    break

            if not url:
                # 构建默认URL (使用SHA256替代MD5)
                item_id = item.get("id", hashlib.sha256(title.encode()).hexdigest()[:8])
                url = f"{news_source.url}#{item_id}"

            # 生成URL哈希 (使用SHA256替代MD5)
            url_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()

            # 内容字段
            content_fields = ["content", "description", "summary", "text"]
            content = ""
            for field in content_fields:
                if field in item and item[field]:
                    content = str(item[field])
                    break

            summary = content[:500] if content else title[:200]

            # 时间字段
            time_fields = ["published_at", "created_at", "date", "time", "pub_date"]
            published_at = datetime.now(tz=timezone.utc)
            for field in time_fields:
                if field in item and item[field]:
                    try:
                        time_val = item[field]
                        if isinstance(time_val, str):
                            published_at = datetime.fromisoformat(
                                time_val.replace("Z", "+00:00")
                            )
                        elif isinstance(time_val, (int, float)):
                            published_at = datetime.fromtimestamp(
                                time_val, tz=timezone.utc
                            )
                        break
                    except BaseException:
                        continue

            article_data = {
                "title": self._clean_text(title),
                "url": url,
                "url_hash": url_hash,
                "content": self._clean_text(content),
                "summary": self._clean_text(summary),
                "author": item.get("author", ""),
                "source_id": news_source.id,
                "source_name": news_source.name,
                "published_at": published_at,
                "language": news_source.language,
                "region": news_source.region,
                "status": ArticleStatus.PENDING.value,
                "word_count": len(content) if content else len(title),
            }

            return article_data

        except Exception as e:
            logger.error(f"解析通用API条目失败: {e}")
            return None

    def _clean_text(self, text: str) -> str:
        """清理文本内容"""
        if not text:
            return ""

        # 移除HTML标签
        text = re.sub(r"<[^>]+>", "", text)
        # 移除特殊字符
        text = re.sub(r"[\r\n\t]+", " ", text)
        # 规范化空白字符
        text = " ".join(text.split())
        return text.strip()
