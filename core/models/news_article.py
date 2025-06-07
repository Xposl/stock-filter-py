#!/usr/bin/env python3

import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union

import aiohttp
from bs4 import BeautifulSoup
from newspaper import Article
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)


class ArticleStatus(str, Enum):
    """文章状态枚举"""

    PENDING = "pending"  # 待处理
    PROCESSING = "processing"  # 处理中
    PROCESSED = "processed"  # 已处理
    FAILED = "failed"  # 处理失败
    ARCHIVED = "archived"  # 已归档


class NewsArticleBase(BaseModel):
    """新闻文章基础模型，包含共有字段"""

    title: str = Field(..., description="文章标题")
    url: str = Field(..., description="文章URL")
    url_hash: str = Field(..., description="URL哈希（去重用）")
    content: Optional[str] = Field(default=None, description="文章正文内容（数据库中可能为NULL）")
    summary: Optional[str] = Field(default=None, description="文章摘要")
    author: Optional[str] = Field(default=None, description="作者")
    source_id: int = Field(..., description="新闻源ID")
    source_name: Optional[str] = Field(default=None, description="来源名称")
    category: Optional[str] = Field(default=None, description="文章分类")
    published_at: Optional[datetime] = Field(default=None, description="发布时间")
    crawled_at: Optional[datetime] = Field(
        default_factory=datetime.now, description="抓取时间"
    )
    language: str = Field(default="zh", description="语言代码")
    region: str = Field(default="CN", description="地区代码")
    entities: Optional[list[dict[str, Any]]] = Field(default=None, description="实体识别结果")
    keywords: Optional[list[str]] = Field(default=None, description="关键词提取结果")
    sentiment_score: Optional[float] = Field(default=None, description="情感分析得分 (-1到1)")
    topics: Optional[list[dict[str, Any]]] = Field(default=None, description="主题分析结果")
    importance_score: float = Field(default=0.0, description="重要性评分 (0-1)")
    market_relevance_score: float = Field(default=0.0, description="市场相关性评分 (0-1)")
    status: ArticleStatus = Field(default=ArticleStatus.PENDING, description="处理状态")
    processed_at: Optional[datetime] = Field(default=None, description="处理完成时间")
    error_message: Optional[str] = Field(default=None, description="处理错误信息")
    word_count: int = Field(default=0, description="字数统计")
    read_time_minutes: int = Field(default=0, description="预计阅读时间（分钟）")

    model_config = ConfigDict(from_attributes=True)


class NewsArticleCreate(BaseModel):
    """用于创建新闻文章的模型"""

    title: str = Field(..., description="文章标题")
    url: str = Field(..., description="文章URL")
    url_hash: Optional[str] = Field(default=None, description="URL哈希（去重用），如果为空会自动生成")
    content: Optional[str] = Field(default=None, description="文章正文内容")
    summary: Optional[str] = Field(default=None, description="文章摘要")
    author: Optional[str] = Field(default=None, description="作者")
    source_id: int = Field(..., description="新闻源ID")
    source_name: Optional[str] = Field(default=None, description="来源名称")
    category: Optional[str] = Field(default=None, description="文章分类")
    published_at: Optional[datetime] = Field(default=None, description="发布时间")
    crawled_at: Optional[datetime] = Field(
        default_factory=datetime.now, description="抓取时间"
    )
    language: str = Field(default="zh", description="语言代码")
    region: str = Field(default="CN", description="地区代码")
    entities: Optional[list[dict[str, Any]]] = Field(default=None, description="实体识别结果")
    keywords: Optional[list[str]] = Field(default=None, description="关键词提取结果")
    sentiment_score: Optional[float] = Field(default=None, description="情感分析得分 (-1到1)")
    topics: Optional[list[dict[str, Any]]] = Field(default=None, description="主题分析结果")
    importance_score: float = Field(default=0.0, description="重要性评分 (0-1)")
    market_relevance_score: float = Field(default=0.0, description="市场相关性评分 (0-1)")
    status: ArticleStatus = Field(default=ArticleStatus.PENDING, description="处理状态")
    processed_at: Optional[datetime] = Field(default=None, description="处理完成时间")
    error_message: Optional[str] = Field(default=None, description="处理错误信息")
    word_count: int = Field(default=0, description="字数统计")
    read_time_minutes: int = Field(default=0, description="预计阅读时间（分钟）")

    model_config = ConfigDict(from_attributes=True)


class NewsArticleUpdate(BaseModel):
    """用于更新新闻文章的模型，所有字段都是可选的"""

    title: Optional[str] = Field(default=None, description="文章标题")
    url: Optional[str] = Field(default=None, description="文章URL")
    url_hash: Optional[str] = Field(default=None, description="URL哈希（去重用）")
    content: Optional[str] = Field(default=None, description="文章正文内容")
    summary: Optional[str] = Field(default=None, description="文章摘要")
    author: Optional[str] = Field(default=None, description="作者")
    source_id: Optional[int] = Field(default=None, description="新闻源ID")
    source_name: Optional[str] = Field(default=None, description="来源名称")
    category: Optional[str] = Field(default=None, description="文章分类")
    published_at: Optional[datetime] = Field(default=None, description="发布时间")
    crawled_at: Optional[datetime] = Field(default=None, description="抓取时间")
    language: Optional[str] = Field(default=None, description="语言代码")
    region: Optional[str] = Field(default=None, description="地区代码")
    entities: Optional[list[dict[str, Any]]] = Field(default=None, description="实体识别结果")
    keywords: Optional[list[str]] = Field(default=None, description="关键词提取结果")
    sentiment_score: Optional[float] = Field(default=None, description="情感分析得分 (-1到1)")
    topics: Optional[list[dict[str, Any]]] = Field(default=None, description="主题分析结果")
    importance_score: Optional[float] = Field(default=None, description="重要性评分 (0-1)")
    market_relevance_score: Optional[float] = Field(
        default=None, description="市场相关性评分 (0-1)"
    )
    status: Optional[ArticleStatus] = Field(default=None, description="处理状态")
    processed_at: Optional[datetime] = Field(default=None, description="处理完成时间")
    error_message: Optional[str] = Field(default=None, description="处理错误信息")
    word_count: Optional[int] = Field(default=None, description="字数统计")
    read_time_minutes: Optional[int] = Field(default=None, description="预计阅读时间（分钟）")

    model_config = ConfigDict(from_attributes=True)


class NewsArticle(NewsArticleBase):
    """完整的新闻文章模型，包含ID"""

    id: int = Field(..., description="ID")
    created_at: Optional[datetime] = Field(
        default_factory=datetime.now, description="创建时间"
    )
    updated_at: Optional[datetime] = Field(
        default_factory=datetime.now, description="更新时间"
    )

    model_config = ConfigDict(from_attributes=True)

    async def get_content_if_missing(
        self, force_refresh: bool = False
    ) -> Optional[str]:
        """
        🔥 动态获取新闻内容（如果数据库中缺失或需要刷新）

        Args:
            force_refresh: 是否强制刷新内容，即使已存在

        Returns:
            获取到的内容或None
        """
        # 如果已有内容且不强制刷新，直接返回
        if self.content and self.content.strip() and not force_refresh:
            return self.content

        logger.info(f"开始获取新闻内容: {self.url}")

        try:
            # 方法1: 尝试使用newspaper3k
            content = await self._fetch_with_newspaper()
            if content:
                # 更新当前对象的content字段
                self.content = content
                self.word_count = len(content)
                self.read_time_minutes = max(1, len(content) // 200)
                logger.info(f"✅ 使用newspaper3k获取内容成功: {len(content)}字符")
                return content

            # 方法2: 回退到requests + BeautifulSoup
            content = await self._fetch_with_requests()
            if content:
                self.content = content
                self.word_count = len(content)
                self.read_time_minutes = max(1, len(content) // 200)
                logger.info(f"✅ 使用requests获取内容成功: {len(content)}字符")
                return content

            logger.warning(f"⚠️ 无法获取新闻内容: {self.url}")
            return None

        except Exception as e:
            logger.error(f"❌ 获取新闻内容失败: {self.url} - {e}")
            return None

    async def _fetch_with_newspaper(self) -> Optional[str]:
        """使用newspaper3k获取内容"""
        try:
            article = Article(self.url, language="zh")
            article.download()
            article.parse()

            if article.text and len(article.text.strip()) > 100:
                return article.text.strip()
            return None

        except Exception as e:
            logger.debug(f"newspaper3k获取失败: {e}")
            return None

    async def _fetch_with_requests(self) -> Optional[str]:
        """使用requests + BeautifulSoup获取内容"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            # 使用aiohttp异步请求
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.url, headers=headers, timeout=10
                ) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, "html.parser")

                        # 尝试多种内容提取策略
                        content = self._extract_content_from_soup(soup)
                        if content and len(content.strip()) > 100:
                            return content.strip()

            return None

        except Exception as e:
            logger.debug(f"requests获取失败: {e}")
            return None

    def _extract_content_from_soup(self, soup: BeautifulSoup) -> Optional[str]:
        """从BeautifulSoup对象中提取文章内容"""
        try:
            # 策略1: 尝试常见的文章内容选择器
            content_selectors = [
                "article",
                ".article-content",
                ".post-content",
                ".content",
                ".main-content",
                '[class*="content"]',
                "main",
                ".article-body",
                ".post-body",
            ]

            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = elements[0].get_text(strip=True)
                    if len(content) > 100:
                        return content

            # 策略2: 回退到body中最长的文本段落
            paragraphs = soup.find_all(["p", "div"])
            longest_text = ""
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > len(longest_text):
                    longest_text = text

            if len(longest_text) > 100:
                return longest_text

            return None

        except Exception as e:
            logger.debug(f"内容提取失败: {e}")
            return None

    def get_analysis_content(self) -> str:
        """
        🔥 获取用于分析的内容文本

        Returns:
            用于分析的完整文本（标题+摘要+内容）
        """
        content_parts = []

        # 优先级1: 标题（权重最高）
        if self.title:
            content_parts.append(f"【标题】{self.title}")

        # 优先级2: 摘要
        if self.summary:
            content_parts.append(f"【摘要】{self.summary}")

        # 优先级3: 正文内容
        if self.content:
            # 限制内容长度，避免token超限
            content_text = (
                self.content[:3000] if len(self.content) > 3000 else self.content
            )
            content_parts.append(f"【正文】{content_text}")
        else:
            # 如果没有内容，至少使用URL作为参考
            content_parts.append(f"【来源】{self.url}")

        # 优先级4: 关键词（如果存在）
        if self.keywords and isinstance(self.keywords, list):
            keywords_text = "、".join(self.keywords[:10])  # 取前10个关键词
            content_parts.append(f"【关键词】{keywords_text}")

        # 优先级5: 实体信息（如果存在）
        if self.entities and isinstance(self.entities, list):
            entities_text = []
            for entity in self.entities[:5]:  # 取前5个实体
                if isinstance(entity, dict) and "name" in entity:
                    entities_text.append(entity["name"])
            if entities_text:
                content_parts.append(f"【实体】{', '.join(entities_text)}")

        return "\n\n".join(content_parts)


# 用于序列化和反序列化的辅助函数
def news_article_to_dict(
    article: Union[NewsArticle, NewsArticleCreate, NewsArticleUpdate]
) -> dict:
    """
    将NewsArticle模型转换为字典，用于数据库操作

    Args:
        article: NewsArticle、NewsArticleCreate或NewsArticleUpdate模型

    Returns:
        字典表示
    """
    result = {}

    if isinstance(article, (NewsArticleCreate, NewsArticleUpdate)):
        result = article.model_dump(exclude_unset=True, exclude_none=True)
    else:
        result = article.model_dump(exclude_none=True)

    # 处理枚举字段
    if "status" in result and isinstance(result["status"], ArticleStatus):
        result["status"] = result["status"].value

    # 处理JSON字段
    json_fields = ["entities", "keywords", "topics"]
    for field in json_fields:
        if field in result and result[field] is not None:
            result[field] = json.dumps(result[field], ensure_ascii=False)

    return result


def dict_to_news_article(data: dict) -> NewsArticle:
    """
    将字典转换为NewsArticle模型，处理各种数据类型转换和默认值

    Args:
        data: 来自数据库的字典数据

    Returns:
        NewsArticle模型实例
    """
    # 创建数据的副本，避免修改原始数据
    processed_data = data.copy()

    # 处理枚举字段
    if "status" in processed_data:
        status = processed_data["status"]
        if isinstance(status, str):
            try:
                processed_data["status"] = ArticleStatus(status)
            except ValueError:
                processed_data["status"] = ArticleStatus.PENDING

    # 处理JSON字段
    json_fields = ["entities", "keywords", "topics"]
    for json_field in json_fields:
        if json_field in processed_data:
            json_value = processed_data[json_field]

            # 如果是None或空字符串，设为None
            if json_value is None or (
                isinstance(json_value, str) and not json_value.strip()
            ):
                processed_data[json_field] = None
            # 如果已经是列表或字典对象，保持不变
            elif isinstance(json_value, (list, dict)):
                pass
            # 尝试解析JSON字符串
            elif isinstance(json_value, str):
                try:
                    processed_data[json_field] = json.loads(json_value)
                except (ValueError, json.JSONDecodeError):
                    processed_data[json_field] = None

    # 确保必要字段存在并有默认值
    processed_data["importance_score"] = float(
        processed_data.get("importance_score", 0.0) or 0.0
    )
    processed_data["market_relevance_score"] = float(
        processed_data.get("market_relevance_score", 0.0) or 0.0
    )
    processed_data["word_count"] = int(processed_data.get("word_count", 0) or 0)
    processed_data["read_time_minutes"] = int(
        processed_data.get("read_time_minutes", 0) or 0
    )
    processed_data["language"] = processed_data.get("language", "zh") or "zh"
    processed_data["region"] = processed_data.get("region", "CN") or "CN"

    # 处理浮点数字段
    if (
        "sentiment_score" in processed_data
        and processed_data["sentiment_score"] is not None
    ):
        try:
            processed_data["sentiment_score"] = float(processed_data["sentiment_score"])
        except (ValueError, TypeError):
            processed_data["sentiment_score"] = None

    # 处理日期字段
    date_fields = [
        "published_at",
        "crawled_at",
        "processed_at",
        "created_at",
        "updated_at",
    ]
    for date_field in date_fields:
        if date_field in processed_data:
            date_value = processed_data[date_field]

            # 如果是None或空字符串，设为None（除了crawled_at）
            if date_value is None or (
                isinstance(date_value, str) and not date_value.strip()
            ):
                if date_field == "crawled_at":
                    processed_data[date_field] = datetime.now()
                else:
                    processed_data[date_field] = None
                continue

            # 如果已经是datetime对象，保持不变
            if isinstance(date_value, datetime):
                continue

            # 尝试将字符串转换为datetime
            if isinstance(date_value, str):
                try:
                    # 尝试ISO格式
                    processed_data[date_field] = datetime.fromisoformat(
                        date_value.replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    try:
                        # 尝试标准MySQL格式
                        processed_data[date_field] = datetime.strptime(
                            date_value, "%Y-%m-%d %H:%M:%S"
                        )
                    except (ValueError, AttributeError):
                        if date_field == "crawled_at":
                            processed_data[date_field] = datetime.now()
                        else:
                            processed_data[date_field] = None

    try:
        # 创建NewsArticle模型实例
        return NewsArticle(**processed_data)
    except Exception as e:
        print(f"无法创建NewsArticle模型: {e}")
        print(f"数据: {processed_data}")

        # 返回带有最小必要字段的NewsArticle（用于错误恢复）
        return NewsArticle(
            id=processed_data.get("id", 0),
            title=processed_data.get("title", "Unknown Title"),
            url=processed_data.get("url", "http://example.com"),
            url_hash=processed_data.get("url_hash", "unknown_hash"),
            source_id=processed_data.get("source_id", 0),
            status=ArticleStatus.PENDING,
        )
