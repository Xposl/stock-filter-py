#!/usr/bin/env python3

"""
情感分析专用工作流

基于PocketFlow框架的情感分析专用流水线：
1. 文本预处理 - 清理和标准化新闻文本
2. 关键词情感分析 - 基于金融情感词典的快速评估
3. 上下文情感分析 - 基于语义理解的深度情感分析
4. 情感评分综合 - 多维度情感评分和置信度计算
"""

import logging
import re
from datetime import datetime
from typing import Any

from pocketflow import AsyncFlow, AsyncNode

logger = logging.getLogger(__name__)


class TextPreprocessingNode(AsyncNode):
    """
    文本预处理节点
    清理和标准化新闻文本，为情感分析做准备
    """

    def __init__(self):
        super().__init__()
        # 清理规则
        self.noise_patterns = [
            r"[\u200b-\u200d\ufeff]",  # 零宽字符
            r"【.*?】",  # 中文方括号内容
            r"\[.*?\]",  # 方括号内容
            r"<.*?>",  # HTML标签
            r"http[s]?://\S+",  # URL链接
            r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}",  # 时间戳
        ]

        # 标准化规则
        self.normalization_rules = {
            "％": "%",
            "＋": "+",
            "－": "-",
            "（": "(",
            "）": ")",
            "，": ",",
            "。": ".",
            "！": "!",
            "？": "?",
            "：": ":",
            "；": ";",
        }

    async def run_async(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        文本预处理逻辑

        Args:
            data: 包含articles列表的输入数据

        Returns:
            预处理后的文章数据
        """
        articles = data.get("articles", [])
        processed_articles = []

        for article in articles:
            processed_article = self._preprocess_article(article)
            processed_articles.append(processed_article)

        logger.info(f"文本预处理完成: {len(processed_articles)} 篇文章")

        return {
            **data,
            "processed_articles": processed_articles,
            "preprocessing_count": len(processed_articles),
        }

    def _preprocess_article(self, article: dict[str, Any]) -> dict[str, Any]:
        """预处理单篇文章"""
        processed = article.copy()

        # 处理标题
        title = article.get("title", "")
        processed["clean_title"] = self._clean_text(title)

        # 处理内容
        content = article.get("content", "")
        processed["clean_content"] = self._clean_text(content)

        # 提取关键句子（前3句和后2句）
        sentences = self._extract_key_sentences(processed["clean_content"])
        processed["key_sentences"] = sentences

        # 计算文本长度
        processed["text_length"] = len(processed["clean_title"]) + len(
            processed["clean_content"]
        )

        return processed

    def _clean_text(self, text: str) -> str:
        """清理和标准化文本"""
        if not text:
            return ""

        # 移除噪声
        for pattern in self.noise_patterns:
            text = re.sub(pattern, "", text)

        # 标准化字符
        for old_char, new_char in self.normalization_rules.items():
            text = text.replace(old_char, new_char)

        # 移除多余空白
        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _extract_key_sentences(self, content: str, max_sentences: int = 5) -> list[str]:
        """提取关键句子"""
        if not content:
            return []

        # 简单的句子分割
        sentences = re.split(r"[.。!！?？;；]", content)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

        if len(sentences) <= max_sentences:
            return sentences

        # 取前3句和后2句
        key_sentences = sentences[:3] + sentences[-2:]
        return key_sentences


class KeywordSentimentNode(AsyncNode):
    """
    关键词情感分析节点
    基于金融情感词典进行快速情感评估
    """

    def __init__(self):
        super().__init__()
        # 金融情感词典
        self.sentiment_dict = {
            "positive": {
                "strong": ["暴涨", "大涨", "飞涨", "暴升", "爆发", "突破", "创新高", "翻倍"],
                "medium": ["上涨", "上升", "增长", "攀升", "走强", "反弹", "好转", "改善"],
                "weak": ["微涨", "小涨", "略涨", "企稳", "向好", "乐观", "正面", "利好"],
            },
            "negative": {
                "strong": ["暴跌", "大跌", "跌停", "崩盘", "暴跌", "血洗", "重挫", "腰斩"],
                "medium": ["下跌", "下降", "下滑", "走弱", "回调", "调整", "疲软", "不振"],
                "weak": ["微跌", "小跌", "略跌", "震荡", "谨慎", "担忧", "风险", "压力"],
            },
            "neutral": ["平稳", "持平", "横盘", "整理", "观望", "等待", "关注", "监控"],
        }

        # 情感强度权重
        self.intensity_weights = {
            "strong": 3.0,
            "medium": 2.0,
            "weak": 1.0,
            "neutral": 0.0,
        }

        # 否定词
        self.negation_words = ["不", "未", "没", "非", "无", "否", "别", "勿"]

    async def run_async(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        关键词情感分析逻辑

        Args:
            data: 包含processed_articles的数据

        Returns:
            关键词情感分析结果
        """
        articles = data.get("processed_articles", [])
        keyword_results = []

        for article in articles:
            sentiment_result = self._analyze_keyword_sentiment(article)
            keyword_results.append(sentiment_result)

        logger.info(f"关键词情感分析完成: {len(keyword_results)} 篇文章")

        return {
            **data,
            "keyword_sentiment_results": keyword_results,
            "keyword_analysis_count": len(keyword_results),
        }

    def _analyze_keyword_sentiment(self, article: dict[str, Any]) -> dict[str, Any]:
        """分析单篇文章的关键词情感"""
        title = article.get("clean_title", "")
        content = article.get("clean_content", "")
        text = f"{title} {content}"

        # 检测情感词汇
        sentiment_matches = self._detect_sentiment_words(text)

        # 计算情感评分
        sentiment_score = self._calculate_sentiment_score(sentiment_matches, text)

        # 提取关键短语
        key_phrases = self._extract_sentiment_phrases(text, sentiment_matches)

        return {
            "article_index": article.get("article_index", 0),
            "sentiment_matches": sentiment_matches,
            "keyword_sentiment_score": sentiment_score,
            "sentiment_label": self._get_sentiment_label(sentiment_score),
            "key_phrases": key_phrases,
            "confidence": self._calculate_confidence(sentiment_matches),
            "dominant_emotion": self._get_dominant_emotion(sentiment_matches),
        }

    def _detect_sentiment_words(self, text: str) -> dict[str, list[str]]:
        """检测文本中的情感词汇"""
        matches = {
            "positive": {"strong": [], "medium": [], "weak": []},
            "negative": {"strong": [], "medium": [], "weak": []},
            "neutral": [],
        }

        # 检测正面和负面情感词
        for sentiment_type in ["positive", "negative"]:
            for intensity in ["strong", "medium", "weak"]:
                words = self.sentiment_dict[sentiment_type][intensity]
                for word in words:
                    if word in text:
                        matches[sentiment_type][intensity].append(word)

        # 检测中性词
        for word in self.sentiment_dict["neutral"]:
            if word in text:
                matches["neutral"].append(word)

        return matches

    def _calculate_sentiment_score(self, matches: dict, text: str) -> float:
        """计算情感评分"""
        positive_score = 0
        negative_score = 0

        # 计算正面评分
        for intensity, words in matches["positive"].items():
            weight = self.intensity_weights[intensity]
            for word in words:
                # 检查否定词
                if self._has_negation_before(text, word):
                    negative_score += weight  # 否定的正面词变成负面
                else:
                    positive_score += weight

        # 计算负面评分
        for intensity, words in matches["negative"].items():
            weight = self.intensity_weights[intensity]
            for word in words:
                # 检查否定词
                if self._has_negation_before(text, word):
                    positive_score += weight  # 否定的负面词变成正面
                else:
                    negative_score += weight

        # 计算最终评分 (-10 到 +10)
        net_score = positive_score - negative_score

        # 标准化到-10到+10范围
        normalized_score = max(-10, min(10, net_score))

        return normalized_score

    def _has_negation_before(self, text: str, word: str) -> bool:
        """检查词汇前是否有否定词"""
        word_index = text.find(word)
        if word_index == -1:
            return False

        # 检查前5个字符内是否有否定词
        prefix = text[max(0, word_index - 5) : word_index]
        return any(neg_word in prefix for neg_word in self.negation_words)

    def _extract_sentiment_phrases(self, text: str, matches: dict) -> list[str]:
        """提取包含情感词的短语"""
        phrases = []

        # 收集所有情感词
        all_sentiment_words = []
        for sentiment_type in ["positive", "negative"]:
            for intensity_words in matches[sentiment_type].values():
                all_sentiment_words.extend(intensity_words)
        all_sentiment_words.extend(matches["neutral"])

        # 为每个情感词提取上下文
        for word in all_sentiment_words:
            phrase = self._extract_phrase_around_word(text, word)
            if phrase:
                phrases.append(phrase)

        return phrases[:5]  # 限制数量

    def _extract_phrase_around_word(
        self, text: str, word: str, context_length: int = 20
    ) -> str:
        """提取词汇周围的短语"""
        word_index = text.find(word)
        if word_index == -1:
            return ""

        start = max(0, word_index - context_length)
        end = min(len(text), word_index + len(word) + context_length)

        phrase = text[start:end].strip()
        return phrase

    def _get_sentiment_label(self, score: float) -> str:
        """获取情感标签"""
        if score > 3:
            return "强烈积极"
        elif score > 1:
            return "积极"
        elif score > -1:
            return "中性"
        elif score > -3:
            return "消极"
        else:
            return "强烈消极"

    def _calculate_confidence(self, matches: dict) -> float:
        """计算分析置信度"""
        total_matches = 0

        for sentiment_type in ["positive", "negative"]:
            for words in matches[sentiment_type].values():
                total_matches += len(words)
        total_matches += len(matches["neutral"])

        # 基于匹配数量计算置信度
        if total_matches >= 5:
            return 0.9
        elif total_matches >= 3:
            return 0.7
        elif total_matches >= 1:
            return 0.5
        else:
            return 0.2

    def _get_dominant_emotion(self, matches: dict) -> str:
        """获取主导情感类型"""
        positive_count = sum(len(words) for words in matches["positive"].values())
        negative_count = sum(len(words) for words in matches["negative"].values())
        neutral_count = len(matches["neutral"])

        if positive_count > negative_count and positive_count > neutral_count:
            return "positive"
        elif negative_count > positive_count and negative_count > neutral_count:
            return "negative"
        else:
            return "neutral"


class ContextualSentimentNode(AsyncNode):
    """
    上下文情感分析节点
    基于语义理解进行深度情感分析
    """

    def __init__(self, llm_client=None):
        super().__init__()
        self.llm_client = llm_client

    async def run_async(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        上下文情感分析逻辑

        Args:
            data: 包含keyword_sentiment_results的数据

        Returns:
            上下文情感分析结果
        """
        articles = data.get("processed_articles", [])
        keyword_results = data.get("keyword_sentiment_results", [])

        if not self.llm_client:
            # 使用简化的启发式方法
            contextual_results = await self._heuristic_contextual_analysis(
                articles, keyword_results
            )
        else:
            # 使用LLM进行深度分析
            contextual_results = await self._llm_contextual_analysis(
                articles, keyword_results
            )

        logger.info(f"上下文情感分析完成: {len(contextual_results)} 篇文章")

        return {
            **data,
            "contextual_sentiment_results": contextual_results,
            "contextual_analysis_count": len(contextual_results),
        }

    async def _heuristic_contextual_analysis(
        self, articles: list[dict], keyword_results: list[dict]
    ) -> list[dict]:
        """启发式上下文分析"""
        results = []

        for i, (article, keyword_result) in enumerate(zip(articles, keyword_results)):
            # 分析上下文因素
            context_factors = self._analyze_context_factors(article)

            # 计算上下文调整后的情感评分
            base_score = keyword_result.get("keyword_sentiment_score", 0)
            adjusted_score = self._adjust_score_by_context(base_score, context_factors)

            result = {
                "article_index": i,
                "context_factors": context_factors,
                "base_sentiment_score": base_score,
                "contextual_sentiment_score": adjusted_score,
                "context_confidence": context_factors.get("confidence", 0.5),
                "sentiment_reasoning": context_factors.get("reasoning", []),
            }

            results.append(result)

        return results

    def _analyze_context_factors(self, article: dict[str, Any]) -> dict[str, Any]:
        """分析上下文因素"""
        title = article.get("clean_title", "")
        content = article.get("clean_content", "")
        text = f"{title} {content}"

        factors = {
            "time_sensitivity": self._analyze_time_sensitivity(text),
            "market_scope": self._analyze_market_scope(text),
            "certainty_level": self._analyze_certainty_level(text),
            "impact_magnitude": self._analyze_impact_magnitude(text),
            "confidence": 0.6,
            "reasoning": [],
        }

        # 基于因素调整置信度
        factor_count = sum(
            1
            for v in factors.values()
            if isinstance(v, dict) and v.get("detected", False)
        )
        factors["confidence"] = min(0.9, 0.4 + factor_count * 0.1)

        return factors

    def _analyze_time_sensitivity(self, text: str) -> dict[str, Any]:
        """分析时间敏感性"""
        time_indicators = {
            "immediate": ["今日", "今天", "刚刚", "立即", "马上", "现在"],
            "short_term": ["本周", "近期", "短期", "即将", "很快"],
            "long_term": ["长期", "未来", "计划", "预期", "目标"],
        }

        for category, words in time_indicators.items():
            if any(word in text for word in words):
                return {"category": category, "detected": True}

        return {"category": "unspecified", "detected": False}

    def _analyze_market_scope(self, text: str) -> dict[str, Any]:
        """分析市场范围"""
        scope_indicators = {
            "individual": ["个股", "单独", "某公司", "该股"],
            "sector": ["板块", "行业", "板", "类股"],
            "market": ["大盘", "市场", "整体", "全面", "普遍"],
        }

        for category, words in scope_indicators.items():
            if any(word in text for word in words):
                return {"category": category, "detected": True}

        return {"category": "unspecified", "detected": False}

    def _analyze_certainty_level(self, text: str) -> dict[str, Any]:
        """分析确定性水平"""
        certainty_indicators = {
            "high": ["确定", "肯定", "明确", "宣布", "公布", "决定"],
            "medium": ["可能", "预计", "估计", "或将", "有望"],
            "low": ["传言", "据说", "可能", "或许", "推测", "猜测"],
        }

        for level, words in certainty_indicators.items():
            if any(word in text for word in words):
                return {"level": level, "detected": True}

        return {"level": "unspecified", "detected": False}

    def _analyze_impact_magnitude(self, text: str) -> dict[str, Any]:
        """分析影响程度"""
        magnitude_indicators = {
            "major": ["重大", "巨大", "显著", "大幅", "大规模", "全面"],
            "moderate": ["一定", "相当", "明显", "较大", "适度"],
            "minor": ["轻微", "小幅", "略微", "有限", "局部"],
        }

        for level, words in magnitude_indicators.items():
            if any(word in text for word in words):
                return {"level": level, "detected": True}

        return {"level": "unspecified", "detected": False}

    def _adjust_score_by_context(
        self, base_score: float, context_factors: dict
    ) -> float:
        """根据上下文因素调整情感评分"""
        adjusted_score = base_score

        # 时间敏感性调整
        time_sensitivity = context_factors.get("time_sensitivity", {})
        if time_sensitivity.get("detected"):
            if time_sensitivity["category"] == "immediate":
                adjusted_score *= 1.2  # 立即性增强情感强度
            elif time_sensitivity["category"] == "long_term":
                adjusted_score *= 0.8  # 长期性降低情感强度

        # 确定性水平调整
        certainty = context_factors.get("certainty_level", {})
        if certainty.get("detected"):
            if certainty["level"] == "high":
                adjusted_score *= 1.1
            elif certainty["level"] == "low":
                adjusted_score *= 0.7

        # 影响程度调整
        impact = context_factors.get("impact_magnitude", {})
        if impact.get("detected"):
            if impact["level"] == "major":
                adjusted_score *= 1.3
            elif impact["level"] == "minor":
                adjusted_score *= 0.8

        # 确保在合理范围内
        return max(-10, min(10, adjusted_score))

    async def _llm_contextual_analysis(
        self, articles: list[dict], keyword_results: list[dict]
    ) -> list[dict]:
        """使用LLM进行上下文情感分析"""
        # TODO: 实现LLM上下文分析
        # 此处可以调用千问LLM进行更深度的语义理解
        return await self._heuristic_contextual_analysis(articles, keyword_results)


class SentimentIntegrationNode(AsyncNode):
    """
    情感评分综合节点
    整合多维度情感分析结果，生成最终的情感评分
    """

    async def run_async(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        情感评分综合逻辑

        Args:
            data: 包含各层情感分析结果的数据

        Returns:
            综合情感评分结果
        """
        keyword_results = data.get("keyword_sentiment_results", [])
        contextual_results = data.get("contextual_sentiment_results", [])

        integrated_results = []

        for _i, (keyword_result, contextual_result) in enumerate(
            zip(keyword_results, contextual_results)
        ):
            integrated_result = self._integrate_sentiment_scores(
                keyword_result, contextual_result
            )
            integrated_results.append(integrated_result)

        # 计算整体情感趋势
        overall_sentiment = self._calculate_overall_sentiment(integrated_results)

        logger.info(f"情感评分综合完成: {len(integrated_results)} 篇文章")

        return {
            "integrated_sentiment_results": integrated_results,
            "overall_sentiment_trend": overall_sentiment,
            "sentiment_summary": self._generate_sentiment_summary(integrated_results),
            "analysis_timestamp": datetime.now().isoformat(),
        }

    def _integrate_sentiment_scores(
        self, keyword_result: dict, contextual_result: dict
    ) -> dict[str, Any]:
        """整合关键词和上下文情感分析结果"""
        keyword_score = keyword_result.get("keyword_sentiment_score", 0)
        contextual_score = contextual_result.get("contextual_sentiment_score", 0)

        keyword_confidence = keyword_result.get("confidence", 0.5)
        contextual_confidence = contextual_result.get("context_confidence", 0.5)

        # 加权平均
        total_weight = keyword_confidence + contextual_confidence
        if total_weight > 0:
            final_score = (
                keyword_score * keyword_confidence
                + contextual_score * contextual_confidence
            ) / total_weight
        else:
            final_score = (keyword_score + contextual_score) / 2

        # 计算综合置信度
        final_confidence = min(
            1.0, (keyword_confidence + contextual_confidence) / 2 + 0.1
        )

        return {
            "article_index": keyword_result.get("article_index", 0),
            "keyword_sentiment_score": keyword_score,
            "contextual_sentiment_score": contextual_score,
            "final_sentiment_score": round(final_score, 2),
            "final_sentiment_label": self._get_sentiment_label(final_score),
            "confidence": round(final_confidence, 2),
            "sentiment_breakdown": {
                "keyword_weight": keyword_confidence,
                "contextual_weight": contextual_confidence,
                "dominant_emotion": keyword_result.get("dominant_emotion", "neutral"),
            },
            "key_indicators": {
                "sentiment_phrases": keyword_result.get("key_phrases", []),
                "context_factors": contextual_result.get("context_factors", {}),
            },
        }

    def _calculate_overall_sentiment(self, results: list[dict]) -> dict[str, Any]:
        """计算整体情感趋势"""
        if not results:
            return {"trend": "neutral", "score": 0, "confidence": 0}

        # 计算加权平均
        total_weight = sum(r["confidence"] for r in results)
        if total_weight > 0:
            weighted_score = (
                sum(r["final_sentiment_score"] * r["confidence"] for r in results)
                / total_weight
            )
        else:
            weighted_score = sum(r["final_sentiment_score"] for r in results) / len(
                results
            )

        # 统计情感分布
        sentiment_distribution = {
            "positive": len([r for r in results if r["final_sentiment_score"] > 1]),
            "neutral": len(
                [r for r in results if -1 <= r["final_sentiment_score"] <= 1]
            ),
            "negative": len([r for r in results if r["final_sentiment_score"] < -1]),
        }

        return {
            "trend": self._get_sentiment_label(weighted_score),
            "score": round(weighted_score, 2),
            "confidence": round(
                sum(r["confidence"] for r in results) / len(results), 2
            ),
            "distribution": sentiment_distribution,
            "article_count": len(results),
        }

    def _generate_sentiment_summary(self, results: list[dict]) -> dict[str, Any]:
        """生成情感分析摘要"""
        if not results:
            return {}

        # 统计各情感标签数量
        label_counts = {}
        for result in results:
            label = result["final_sentiment_label"]
            label_counts[label] = label_counts.get(label, 0) + 1

        # 找到最强烈的情感
        strongest_sentiment = max(
            results, key=lambda x: abs(x["final_sentiment_score"])
        )

        # 计算平均置信度
        avg_confidence = sum(r["confidence"] for r in results) / len(results)

        return {
            "total_articles": len(results),
            "label_distribution": label_counts,
            "strongest_sentiment": {
                "score": strongest_sentiment["final_sentiment_score"],
                "label": strongest_sentiment["final_sentiment_label"],
                "article_index": strongest_sentiment["article_index"],
            },
            "average_confidence": round(avg_confidence, 2),
            "high_confidence_count": len([r for r in results if r["confidence"] > 0.7]),
        }

    def _get_sentiment_label(self, score: float) -> str:
        """获取情感标签"""
        if score > 5:
            return "极度积极"
        elif score > 2:
            return "积极"
        elif score > -2:
            return "中性"
        elif score > -5:
            return "消极"
        else:
            return "极度消极"


class SentimentAnalysisFlow:
    """
    情感分析主工作流
    使用PocketFlow实现专业的情感分析流水线
    """

    def __init__(self, llm_client=None):
        # 创建处理节点
        self.text_preprocessing = TextPreprocessingNode()
        self.keyword_sentiment = KeywordSentimentNode()
        self.contextual_sentiment = ContextualSentimentNode(llm_client)
        self.sentiment_integration = SentimentIntegrationNode()

    async def analyze_sentiment(self, articles: list[dict[str, Any]]) -> dict[str, Any]:
        """
        执行情感分析

        Args:
            articles: 新闻文章列表

        Returns:
            完整的情感分析结果
        """
        logger.info(f"开始情感分析工作流，输入文章数: {len(articles)}")

        # 创建PocketFlow流水线
        flow = AsyncFlow(start=self.text_preprocessing)
        flow = flow.next(self.keyword_sentiment)
        flow = flow.next(self.contextual_sentiment)
        flow = flow.next(self.sentiment_integration)

        # 执行工作流
        input_data = {"articles": articles}
        result = await flow.run_async(input_data)

        logger.info("情感分析工作流完成")
        return result


# 便捷接口
async def analyze_sentiment_articles(
    articles: list[dict[str, Any]], llm_client=None
) -> dict[str, Any]:
    """
    便捷的情感分析接口

    Args:
        articles: 新闻文章列表
        llm_client: 可选的LLM客户端

    Returns:
        情感分析结果
    """
    flow = SentimentAnalysisFlow(llm_client)
    return await flow.analyze_sentiment(articles)
