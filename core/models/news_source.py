#!/usr/bin/env python3

import json
from datetime import datetime
from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class NewsSourceType(str, Enum):
    """新闻源类型枚举"""

    RSS = "rss"
    API = "api"
    WEBSITE = "website"
    TWITTER = "twitter"


class NewsSourceStatus(str, Enum):
    """新闻源状态枚举"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    SUSPENDED = "suspended"


class NewsSourceBase(BaseModel):
    """新闻源基础模型，包含共有字段"""

    name: str = Field(..., description="新闻源名称")
    description: Optional[str] = Field(default=None, description="新闻源描述")
    source_type: NewsSourceType = Field(..., description="新闻源类型")
    url: str = Field(..., description="新闻源URL")
    api_key: Optional[str] = Field(default=None, description="API密钥")
    update_frequency: int = Field(default=3600, description="更新频率（秒）")
    max_articles_per_fetch: int = Field(default=50, description="每次抓取最大文章数")
    filter_keywords: Optional[list[str]] = Field(default=None, description="关键词过滤")
    filter_categories: Optional[list[str]] = Field(default=None, description="分类过滤")
    language: str = Field(default="zh", description="语言代码")
    region: str = Field(default="CN", description="地区代码")
    status: NewsSourceStatus = Field(default=NewsSourceStatus.ACTIVE, description="状态")
    last_fetch_time: Optional[datetime] = Field(default=None, description="最后抓取时间")
    last_error_message: Optional[str] = Field(default=None, description="最后错误信息")
    total_articles_fetched: int = Field(default=0, description="总抓取文章数")

    model_config = ConfigDict(from_attributes=True)


class NewsSourceCreate(NewsSourceBase):
    """用于创建新闻源的模型"""

    pass


class NewsSourceUpdate(BaseModel):
    """用于更新新闻源的模型，所有字段都是可选的"""

    name: Optional[str] = Field(default=None, description="新闻源名称")
    description: Optional[str] = Field(default=None, description="新闻源描述")
    source_type: Optional[NewsSourceType] = Field(default=None, description="新闻源类型")
    url: Optional[str] = Field(default=None, description="新闻源URL")
    api_key: Optional[str] = Field(default=None, description="API密钥")
    update_frequency: Optional[int] = Field(default=None, description="更新频率（秒）")
    max_articles_per_fetch: Optional[int] = Field(default=None, description="每次抓取最大文章数")
    filter_keywords: Optional[list[str]] = Field(default=None, description="关键词过滤")
    filter_categories: Optional[list[str]] = Field(default=None, description="分类过滤")
    language: Optional[str] = Field(default=None, description="语言代码")
    region: Optional[str] = Field(default=None, description="地区代码")
    status: Optional[NewsSourceStatus] = Field(default=None, description="状态")
    last_fetch_time: Optional[datetime] = Field(default=None, description="最后抓取时间")
    last_error_message: Optional[str] = Field(default=None, description="最后错误信息")
    total_articles_fetched: Optional[int] = Field(default=None, description="总抓取文章数")

    model_config = ConfigDict(from_attributes=True)


class NewsSource(NewsSourceBase):
    """完整的新闻源模型，包含ID"""

    id: int = Field(..., description="ID")
    created_at: Optional[datetime] = Field(
        default_factory=datetime.now, description="创建时间"
    )
    updated_at: Optional[datetime] = Field(
        default_factory=datetime.now, description="更新时间"
    )

    model_config = ConfigDict(from_attributes=True)


# 用于序列化和反序列化的辅助函数
def news_source_to_dict(
    source: Union[NewsSource, NewsSourceCreate, NewsSourceUpdate]
) -> dict:
    """
    将NewsSource模型转换为字典，用于数据库操作

    Args:
        source: NewsSource、NewsSourceCreate或NewsSourceUpdate模型

    Returns:
        字典表示
    """
    result = {}

    if isinstance(source, (NewsSourceCreate, NewsSourceUpdate)):
        result = source.model_dump(exclude_unset=True, exclude_none=True)
    else:
        result = source.model_dump(exclude_none=True)

    # 处理枚举字段
    if "source_type" in result and isinstance(result["source_type"], NewsSourceType):
        result["source_type"] = result["source_type"].value

    if "status" in result and isinstance(result["status"], NewsSourceStatus):
        result["status"] = result["status"].value

    # 处理JSON字段
    if "filter_keywords" in result and result["filter_keywords"] is not None:
        result["filter_keywords"] = json.dumps(
            result["filter_keywords"], ensure_ascii=False
        )

    if "filter_categories" in result and result["filter_categories"] is not None:
        result["filter_categories"] = json.dumps(
            result["filter_categories"], ensure_ascii=False
        )

    return result


def dict_to_news_source(data: dict) -> NewsSource:
    """
    将字典转换为NewsSource模型，处理各种数据类型转换和默认值

    Args:
        data: 来自数据库的字典数据

    Returns:
        NewsSource模型实例
    """
    # 创建数据的副本，避免修改原始数据
    processed_data = data.copy()

    # 处理枚举字段
    if "source_type" in processed_data:
        source_type = processed_data["source_type"]
        if isinstance(source_type, str):
            try:
                processed_data["source_type"] = NewsSourceType(source_type)
            except ValueError:
                processed_data["source_type"] = NewsSourceType.RSS

    if "status" in processed_data:
        status = processed_data["status"]
        if isinstance(status, str):
            try:
                processed_data["status"] = NewsSourceStatus(status)
            except ValueError:
                processed_data["status"] = NewsSourceStatus.ACTIVE

    # 处理JSON字段
    for json_field in ["filter_keywords", "filter_categories"]:
        if json_field in processed_data:
            json_value = processed_data[json_field]

            # 如果是None或空字符串，设为None
            if json_value is None or (
                isinstance(json_value, str) and not json_value.strip()
            ):
                processed_data[json_field] = None
            # 如果已经是列表对象，保持不变
            elif isinstance(json_value, list):
                pass
            # 尝试解析JSON字符串
            elif isinstance(json_value, str):
                try:
                    parsed = json.loads(json_value)
                    processed_data[json_field] = (
                        parsed if isinstance(parsed, list) else None
                    )
                except (ValueError, json.JSONDecodeError):
                    processed_data[json_field] = None

    # 确保必要字段存在并有默认值
    processed_data["update_frequency"] = int(
        processed_data.get("update_frequency", 3600) or 3600
    )
    processed_data["max_articles_per_fetch"] = int(
        processed_data.get("max_articles_per_fetch", 50) or 50
    )
    processed_data["total_articles_fetched"] = int(
        processed_data.get("total_articles_fetched", 0) or 0
    )
    processed_data["language"] = processed_data.get("language", "zh") or "zh"
    processed_data["region"] = processed_data.get("region", "CN") or "CN"

    # 处理日期字段
    for date_field in ["last_fetch_time", "created_at", "updated_at"]:
        if date_field in processed_data:
            date_value = processed_data[date_field]

            # 如果是None或空字符串，设为None
            if date_value is None or (
                isinstance(date_value, str) and not date_value.strip()
            ):
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
                        processed_data[date_field] = None

    try:
        # 创建NewsSource模型实例
        return NewsSource(**processed_data)
    except Exception as e:
        print(f"无法创建NewsSource模型: {e}")
        print(f"数据: {processed_data}")

        # 返回带有最小必要字段的NewsSource（用于错误恢复）
        return NewsSource(
            id=processed_data.get("id", 0),
            name=processed_data.get("name", "Unknown Source"),
            source_type=NewsSourceType.RSS,
            url=processed_data.get("url", "http://example.com"),
            status=NewsSourceStatus.ACTIVE,
        )
