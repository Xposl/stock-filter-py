#!/usr/bin/env python3

"""
数据转换工具模块

专业的数据转换和格式化工具集，支持：
- 新闻数据格式转换和标准化
- 分析结果数据结构转换
- 投资建议数据格式化
- API响应数据转换
- 数据库模型与业务模型转换
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class StandardNewsArticle:
    """标准化新闻文章数据结构"""

    id: Optional[int] = None
    title: str = ""
    content: str = ""
    url: str = ""
    source_name: str = ""
    source_id: Optional[int] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.published_at is None:
            self.published_at = datetime.now(timezone.utc)
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


@dataclass
class StandardAnalysisResult:
    """标准化分析结果数据结构"""

    article_id: int
    sentiment_score: float  # -10 到 +10
    sentiment_label: str
    confidence: float  # 0-1
    key_phrases: list[str]
    investment_opportunities: list[dict[str, Any]]
    risk_factors: list[str]
    recommendations: list[dict[str, Any]]
    analysis_timestamp: datetime
    processing_time: float  # 秒

    def __post_init__(self):
        if self.analysis_timestamp is None:
            self.analysis_timestamp = datetime.now(timezone.utc)


class NewsDataConverter:
    """新闻数据转换器"""

    def __init__(self):
        # 源字段映射
        self.field_mappings = {
            "rss": {
                "title": ["title", "headline"],
                "content": ["description", "content", "summary"],
                "url": ["link", "url"],
                "published": ["pubDate", "published", "date"],
                "author": ["author", "creator"],
            },
            "xueqiu": {
                "title": ["title", "text"],
                "content": ["text", "description"],
                "url": ["target", "url"],
                "published": ["created_at", "timestamp"],
                "author": ["user_name", "screen_name"],
            },
            "api": {
                "title": ["title", "headline", "subject"],
                "content": ["content", "body", "text"],
                "url": ["url", "link", "source_url"],
                "published": ["published_at", "created_at", "timestamp"],
                "author": ["author", "writer", "creator"],
            },
        }
        self.field_mappings = {
            # RSS源映射
            "rss": {
                "title": ["title", "headline", "summary"],
                "content": ["content", "description", "summary", "text"],
                "url": ["link", "url", "guid"],
                "published": ["published", "pubDate", "date", "published_parsed"],
                "author": ["author", "creator", "dc:creator"],
            },
            # 雪球源映射
            "xueqiu": {
                "title": ["title", "text"],
                "content": ["text", "description"],
                "url": ["target", "link"],
                "published": ["created_at", "timeBefore"],
                "author": ["user", "screen_name"],
            },
            # API源映射
            "api": {
                "title": ["title", "headline"],
                "content": ["content", "body", "text"],
                "url": ["url", "link"],
                "published": ["published_at", "publish_time", "date"],
                "author": ["author", "writer"],
            },
        }

    def convert_to_standard(
        self,
        raw_data: dict[str, Any],
        source_type: str = "rss",
        source_name: str = "",
        source_id: Optional[int] = None,
    ) -> StandardNewsArticle:
        """
        转换原始数据为标准格式

        Args:
            raw_data: 原始数据字典
            source_type: 数据源类型 (rss, xueqiu, api)
            source_name: 数据源名称
            source_id: 数据源ID

        Returns:
            标准化的新闻文章对象
        """
        try:
            mapping = self.field_mappings.get(source_type, self.field_mappings["rss"])

            # 提取标题
            title = self._extract_field(raw_data, mapping["title"])

            # 提取内容
            content = self._extract_field(raw_data, mapping["content"])

            # 提取URL
            url = self._extract_field(raw_data, mapping["url"])

            # 提取发布时间
            published_at = self._extract_datetime(raw_data, mapping["published"])

            # 提取作者
            author = self._extract_field(raw_data, mapping["author"])

            # 提取其他字段
            category = raw_data.get("category", "")
            tags = self._extract_tags(raw_data)

            return StandardNewsArticle(
                title=self._clean_text(title),
                content=self._clean_text(content),
                url=self._clean_url(url),
                source_name=source_name,
                source_id=source_id,
                author=author,
                published_at=published_at,
                category=category,
                tags=tags,
            )

        except Exception as e:
            logger.error(f"数据转换失败: {e}")
            # 返回空的标准对象
            return StandardNewsArticle(source_name=source_name, source_id=source_id)

    def _extract_field(self, data: dict, field_names: list[str]) -> str:
        """从数据中提取字段值"""
        for field_name in field_names:
            if field_name in data and data[field_name]:
                value = data[field_name]
                if isinstance(value, dict):
                    # 处理嵌套字典
                    if "value" in value:
                        return str(value["value"])
                    elif "text" in value:
                        return str(value["text"])
                return str(value)
        return ""

    def _extract_datetime(
        self, data: dict, field_names: list[str]
    ) -> Optional[datetime]:
        """提取日期时间字段"""
        for field_name in field_names:
            if field_name in data and data[field_name]:
                value = data[field_name]
                try:
                    if isinstance(value, datetime):
                        return value
                    elif isinstance(value, str):
                        # 尝试解析时间字符串
                        return self._parse_datetime_string(value)
                    elif isinstance(value, (int, float)):
                        # Unix时间戳
                        return datetime.fromtimestamp(value, tz=timezone.utc)
                except Exception as e:
                    logger.warning(f"日期解析失败 {field_name}={value}: {e}")
                    continue

        return datetime.now(timezone.utc)  # 默认当前时间

    def _parse_datetime_string(self, date_str: str) -> datetime:
        """解析日期时间字符串"""
        # 常见的日期格式
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%a, %d %b %Y %H:%M:%S %Z",
            "%Y-%m-%d",
            "%d/%m/%Y %H:%M:%S",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue

        # 如果都解析失败，返回当前时间
        logger.warning(f"无法解析日期字符串: {date_str}")
        return datetime.now(timezone.utc)

    def _extract_tags(self, data: dict) -> list[str]:
        """提取标签"""
        tags = []

        # 从不同字段提取标签
        tag_fields = ["tags", "categories", "keywords", "labels"]

        for field in tag_fields:
            if field in data:
                value = data[field]
                if isinstance(value, list):
                    tags.extend([str(tag) for tag in value])
                elif isinstance(value, str):
                    # 逗号分隔的标签
                    tags.extend([tag.strip() for tag in value.split(",")])

        # 去重并过滤
        return list({tag for tag in tags if tag and len(tag) > 1})

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""

        # 移除HTML标签
        import re

        text = re.sub(r"<[^>]+>", "", text)

        # 移除多余空白
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _clean_url(self, url: str) -> str:
        """清理URL"""
        if not url:
            return ""

        # 基本URL清理
        url = url.strip()

        # 确保有协议
        if url and not url.startswith(("http://", "https://")):
            url = "https://" + url

        return url

    def convert_batch(
        self,
        raw_articles: list[dict[str, Any]],
        source_type: str = "rss",
        source_name: str = "",
        source_id: Optional[int] = None,
    ) -> list[StandardNewsArticle]:
        """批量转换新闻数据"""
        results = []

        for raw_article in raw_articles:
            try:
                standard_article = self.convert_to_standard(
                    raw_article, source_type, source_name, source_id
                )
                results.append(standard_article)
            except Exception as e:
                logger.error(f"批量转换中的单条失败: {e}")
                continue

        logger.info(f"批量转换完成: {len(results)}/{len(raw_articles)} 成功")
        return results


class AnalysisResultConverter:
    """分析结果转换器"""

    def convert_sentiment_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """转换情感分析结果"""
        return {
            "sentiment_score": float(result.get("final_sentiment_score", 0)),
            "sentiment_label": result.get("final_sentiment_label", "中性"),
            "confidence": float(result.get("confidence", 0)),
            "dominant_emotion": result.get("sentiment_breakdown", {}).get(
                "dominant_emotion", "neutral"
            ),
            "key_phrases": result.get("key_indicators", {}).get(
                "sentiment_phrases", []
            ),
            "analysis_details": {
                "keyword_score": result.get("keyword_sentiment_score", 0),
                "contextual_score": result.get("contextual_sentiment_score", 0),
                "breakdown": result.get("sentiment_breakdown", {}),
            },
        }

    def convert_investment_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """转换投资分析结果"""
        advice = result.get("investment_advice", {})

        return {
            "investment_action": advice.get("action", "观望"),
            "position_size": advice.get("position_size", "观望 (0%)"),
            "time_frame": advice.get("time_frame", "中线 (1-3个月)"),
            "confidence": float(advice.get("confidence", 0)),
            "rationale": advice.get("rationale", ""),
            "opportunities": self._extract_opportunities(result),
            "risks": self._extract_risks(result),
            "target_companies": advice.get("target_companies", []),
            "investment_themes": advice.get("investment_themes", []),
        }

    def _extract_opportunities(self, result: dict[str, Any]) -> list[dict[str, Any]]:
        """提取投资机会"""
        analysis_results = result.get("analysis_results", [])
        opportunities = []

        for analysis in analysis_results:
            opp = analysis.get("opportunity")
            if opp:
                opportunities.append(
                    {
                        "type": opp.get("opportunity_type", ""),
                        "industry": opp.get("industry", ""),
                        "score": float(opp.get("score", 0)),
                        "confidence": float(opp.get("confidence", 0)),
                        "time_horizon": opp.get("time_horizon", ""),
                        "key_factors": opp.get("key_factors", []),
                    }
                )

        return opportunities

    def _extract_risks(self, result: dict[str, Any]) -> list[dict[str, Any]]:
        """提取风险因素"""
        analysis_results = result.get("analysis_results", [])
        risks = []

        for analysis in analysis_results:
            risk = analysis.get("risk_assessment")
            if risk:
                risks.append(
                    {
                        "level": risk.get("risk_level", ""),
                        "score": float(risk.get("risk_score", 0)),
                        "factors": risk.get("risk_factors", []),
                        "mitigation": risk.get("mitigation_strategies", []),
                    }
                )

        return risks

    def convert_complete_analysis(
        self,
        article: StandardNewsArticle,
        sentiment_result: dict[str, Any],
        investment_result: dict[str, Any],
        processing_time: float = 0.0,
    ) -> StandardAnalysisResult:
        """转换完整分析结果"""
        sentiment_data = self.convert_sentiment_result(sentiment_result)
        investment_data = self.convert_investment_result(investment_result)

        return StandardAnalysisResult(
            article_id=article.id or 0,
            sentiment_score=sentiment_data["sentiment_score"],
            sentiment_label=sentiment_data["sentiment_label"],
            confidence=sentiment_data["confidence"],
            key_phrases=sentiment_data["key_phrases"],
            investment_opportunities=investment_data["opportunities"],
            risk_factors=[risk["factors"] for risk in investment_data["risks"]],
            recommendations=[
                {
                    "action": investment_data["investment_action"],
                    "position": investment_data["position_size"],
                    "timeframe": investment_data["time_frame"],
                    "rationale": investment_data["rationale"],
                }
            ],
            analysis_timestamp=datetime.now(timezone.utc),
            processing_time=processing_time,
        )


class APIResponseConverter:
    """API响应转换器"""

    def __init__(self):
        self.news_converter = NewsDataConverter()
        self.analysis_converter = AnalysisResultConverter()

    def convert_analysis_response(
        self, analysis_result: StandardAnalysisResult
    ) -> dict[str, Any]:
        """转换分析结果为API响应格式"""
        return {
            "status": "success",
            "data": {
                "article_id": analysis_result.article_id,
                "sentiment": {
                    "score": analysis_result.sentiment_score,
                    "label": analysis_result.sentiment_label,
                    "confidence": analysis_result.confidence,
                },
                "investment": {
                    "opportunities": analysis_result.investment_opportunities,
                    "recommendations": analysis_result.recommendations,
                    "risk_factors": analysis_result.risk_factors,
                },
                "key_insights": {
                    "phrases": analysis_result.key_phrases,
                    "processing_time": analysis_result.processing_time,
                },
                "timestamp": analysis_result.analysis_timestamp.isoformat(),
            },
        }

    def convert_batch_analysis_response(
        self, results: list[StandardAnalysisResult], total_processing_time: float = 0.0
    ) -> dict[str, Any]:
        """转换批量分析结果为API响应格式"""
        converted_results = []

        for result in results:
            converted_results.append(self.convert_analysis_response(result)["data"])

        # 统计摘要
        summary = self._generate_batch_summary(results)

        return {
            "status": "success",
            "data": {
                "results": converted_results,
                "summary": summary,
                "metadata": {
                    "total_articles": len(results),
                    "total_processing_time": total_processing_time,
                    "average_processing_time": total_processing_time
                    / max(1, len(results)),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            },
        }

    def _generate_batch_summary(
        self, results: list[StandardAnalysisResult]
    ) -> dict[str, Any]:
        """生成批量分析摘要"""
        if not results:
            return {}

        # 情感分布统计
        sentiment_scores = [r.sentiment_score for r in results]
        sentiment_labels = [r.sentiment_label for r in results]

        # 投资建议统计
        all_recommendations = []
        for result in results:
            for rec in result.recommendations:
                all_recommendations.append(rec.get("action", ""))

        # 统计分布
        from collections import Counter

        label_counts = Counter(sentiment_labels)
        action_counts = Counter(all_recommendations)

        return {
            "sentiment_overview": {
                "average_score": round(
                    sum(sentiment_scores) / len(sentiment_scores), 2
                ),
                "score_range": [min(sentiment_scores), max(sentiment_scores)],
                "label_distribution": dict(label_counts),
            },
            "investment_overview": {
                "action_distribution": dict(action_counts),
                "total_opportunities": sum(
                    len(r.investment_opportunities) for r in results
                ),
                "actionable_count": len(
                    [
                        r
                        for r in results
                        if any(
                            "买入" in rec.get("action", "") for rec in r.recommendations
                        )
                    ]
                ),
            },
            "confidence_metrics": {
                "average_confidence": round(
                    sum(r.confidence for r in results) / len(results), 2
                ),
                "high_confidence_count": len(
                    [r for r in results if r.confidence >= 0.7]
                ),
            },
        }


class DatabaseModelConverter:
    """数据库模型转换器"""

    def convert_to_dict(self, obj: Any, exclude_none: bool = True) -> dict[str, Any]:
        """将对象转换为字典"""
        if hasattr(obj, "__dict__"):
            data = {}
            for key, value in obj.__dict__.items():
                if exclude_none and value is None:
                    continue

                # 处理datetime对象
                if isinstance(value, datetime):
                    data[key] = value.isoformat()
                # 处理Decimal对象
                elif isinstance(value, Decimal):
                    data[key] = float(value)
                # 处理dataclass对象
                elif hasattr(value, "__dataclass_fields__"):
                    data[key] = asdict(value)
                else:
                    data[key] = value

            return data
        elif hasattr(obj, "__dataclass_fields__"):
            return asdict(obj)
        else:
            return {}

    def convert_from_dict(self, data: dict[str, Any], target_class: type):
        """从字典转换为对象"""
        try:
            # 处理datetime字段
            for key, value in data.items():
                if isinstance(value, str) and key.endswith(("_at", "_time")):
                    try:
                        data[key] = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    except ValueError:
                        pass

            return target_class(**data)
        except Exception as e:
            logger.error(f"对象转换失败 {target_class.__name__}: {e}")
            return None


# 便捷函数
def convert_news_data(
    raw_data: Union[dict, list[dict]],
    source_type: str = "rss",
    source_name: str = "",
    source_id: Optional[int] = None,
) -> Union[StandardNewsArticle, list[StandardNewsArticle]]:
    """便捷的新闻数据转换函数"""
    converter = NewsDataConverter()

    if isinstance(raw_data, list):
        return converter.convert_batch(raw_data, source_type, source_name, source_id)
    else:
        return converter.convert_to_standard(
            raw_data, source_type, source_name, source_id
        )


def convert_analysis_to_api(
    analysis_result: Union[StandardAnalysisResult, list[StandardAnalysisResult]]
) -> dict[str, Any]:
    """便捷的分析结果API转换函数"""
    converter = APIResponseConverter()

    if isinstance(analysis_result, list):
        return converter.convert_batch_analysis_response(analysis_result)
    else:
        return converter.convert_analysis_response(analysis_result)


def convert_to_json(
    obj: Any, ensure_ascii: bool = False, indent: Optional[int] = None
) -> str:
    """便捷的JSON转换函数"""
    converter = DatabaseModelConverter()

    if hasattr(obj, "__dict__") or hasattr(obj, "__dataclass_fields__"):
        data = converter.convert_to_dict(obj)
    else:
        data = obj

    return json.dumps(data, ensure_ascii=ensure_ascii, indent=indent, default=str)
