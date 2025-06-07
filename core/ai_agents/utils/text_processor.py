#!/usr/bin/env python3

"""
文本处理工具模块

专业的文本处理工具集，支持：
- 文本清理和标准化
- 关键词提取和权重计算
- 实体识别和命名实体提取
- 文本特征分析
"""

import logging
import re
from dataclasses import dataclass
from typing import Any

import jieba
import jieba.posseg as pseg

logger = logging.getLogger(__name__)


@dataclass
class TextFeatures:
    """文本特征数据结构"""

    length: int
    sentence_count: int
    word_count: int
    unique_words: int
    avg_sentence_length: float
    complexity_score: float
    financial_terms_count: int


@dataclass
class KeywordResult:
    """关键词提取结果"""

    keyword: str
    weight: float
    frequency: int
    pos_tag: str  # 词性标注
    importance: float  # 重要性评分


@dataclass
class EntityResult:
    """实体识别结果"""

    entity: str
    entity_type: str  # 实体类型
    positions: list[int]  # 在文本中的位置
    confidence: float


class TextCleaner:
    """文本清理器"""

    def __init__(self):
        # 清理规则
        self.noise_patterns = [
            r"[\u200b-\u200d\ufeff]",  # 零宽字符
            r"【.*?】",  # 中文方括号内容
            r"\[.*?\]",  # 英文方括号内容
            r"<.*?>",  # HTML标签
            r"http[s]?://\S+",  # URL链接
            r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}",  # 时间戳
            r'[^\w\s\u4e00-\u9fff.,!?;:()（）、，。！？；：""' "]",  # 保留中英文和标点
        ]

        # 停用词
        self.stop_words = {
                "的",
                "是",
                "在",
                "了",
                "和",
                "有",
                "为",
                "与",
                "等",
                "及",
                "中",
                "上",
                "下",
                "将",
                "由",
                "对",
                "从",
                "以",
                "到",
                "于",
                "按",
                "向",
                "往",
                "所",
                "但",
                "而",
                "这",
                "那",
                "其",
                "该",
                "此",
                "每",
                "各",
                "都",
                "也",
                "还",
                "就",
                "又",
                "更",
                "很",
                "非常",
                "特别",
                "相当",
                "比较",
                "较",
                "更加",
                "十分",
                "极其",
                "他",
                "她",
                "它",
                "我",
                "你",
                "您",
                "咱",
                "大家",
                "人们",
                "自己",
            }

    def clean_text(self, text: str) -> str:
        """
        清理文本

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        if not text:
            return ""

        # 应用清理规则
        cleaned = text
        for pattern in self.noise_patterns:
            cleaned = re.sub(pattern, "", cleaned)

        # 标准化空白字符
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        # 移除过短的内容
        if len(cleaned) < 10:
            return ""

        return cleaned

    def remove_stop_words(self, words: list[str]) -> list[str]:
        """移除停用词"""
        return [word for word in words if word not in self.stop_words and len(word) > 1]

    def normalize_punctuation(self, text: str) -> str:
        """标准化标点符号"""
        # 中文标点转英文标点
        punct_map = {
            "，": ",",
            "。": ".",
            "！": "!",
            "？": "?",
            "；": ";",
            "：": ":",
            '"': '"',
            """: "'", """: "'",
        }

        normalized = text
        for chinese, english in punct_map.items():
            normalized = normalized.replace(chinese, english)

        return normalized


class KeywordExtractor:
    """关键词提取器"""

    def __init__(self):
        self.cleaner = TextCleaner()

        # 金融相关词汇权重
        self.financial_weights = {
            "股票": 2.0,
            "股价": 2.0,
            "股市": 2.0,
            "上市": 1.8,
            "投资": 2.0,
            "收益": 1.8,
            "盈利": 2.0,
            "亏损": 2.0,
            "业绩": 1.8,
            "财报": 1.8,
            "涨": 2.5,
            "跌": 2.5,
            "暴涨": 3.0,
            "暴跌": 3.0,
            "突破": 2.2,
            "政策": 1.8,
            "监管": 1.8,
            "银行": 1.5,
            "基金": 1.5,
            "证券": 1.5,
            "市场": 1.5,
            "经济": 1.5,
            "金融": 1.5,
            "资本": 1.5,
            "融资": 1.8,
            "并购": 2.0,
            "重组": 2.0,
            "合作": 1.5,
            "协议": 1.5,
            "合同": 1.5,
        }

        # 词性权重
        self.pos_weights = {
            "n": 1.0,  # 名词
            "v": 0.8,  # 动词
            "a": 0.9,  # 形容词
            "nr": 1.5,  # 人名
            "ns": 1.3,  # 地名
            "nt": 1.8,  # 机构名
            "nz": 1.2,  # 其他专名
        }

    def extract_keywords(
        self, text: str, top_k: int = 20, min_freq: int = 1
    ) -> list[KeywordResult]:
        """
        提取关键词

        Args:
            text: 输入文本
            top_k: 返回前k个关键词
            min_freq: 最小词频

        Returns:
            关键词列表
        """
        if not text:
            return []

        # 清理文本
        cleaned_text = self.cleaner.clean_text(text)

        # 分词和词性标注
        words_with_pos = pseg.cut(cleaned_text)

        # 统计词频和计算权重
        word_stats = {}
        for word, pos in words_with_pos:
            if len(word) < 2:  # 过滤单字符
                continue

            if word not in word_stats:
                word_stats[word] = {"frequency": 0, "pos": pos, "positions": []}

            word_stats[word]["frequency"] += 1

        # 移除停用词
        filtered_words = {
            word: stats
            for word, stats in word_stats.items()
            if word not in self.cleaner.stop_words and stats["frequency"] >= min_freq
        }

        # 计算关键词权重
        keywords = []
        total_words = len(filtered_words)

        for word, stats in filtered_words.items():
            weight = self._calculate_keyword_weight(
                word, stats["frequency"], stats["pos"], total_words
            )

            importance = self._calculate_importance(word, stats, cleaned_text)

            keywords.append(
                KeywordResult(
                    keyword=word,
                    weight=weight,
                    frequency=stats["frequency"],
                    pos_tag=stats["pos"],
                    importance=importance,
                )
            )

        # 排序并返回前k个
        keywords.sort(key=lambda x: x.weight, reverse=True)
        return keywords[:top_k]

    def _calculate_keyword_weight(
        self, word: str, frequency: int, pos: str, total_words: int
    ) -> float:
        """计算关键词权重"""
        # TF权重
        tf_weight = frequency / max(1, total_words)

        # 词性权重
        pos_weight = self.pos_weights.get(pos, 0.5)

        # 金融词汇权重
        financial_weight = self.financial_weights.get(word, 1.0)

        # 词长度权重（适当偏好较长的词）
        length_weight = min(2.0, len(word) / 3)

        # 综合权重
        total_weight = tf_weight * pos_weight * financial_weight * length_weight

        return round(total_weight, 4)

    def _calculate_importance(self, word: str, stats: dict, text: str) -> float:
        """计算词汇重要性"""
        # 频率重要性
        freq_importance = min(1.0, stats["frequency"] / 10)

        # 位置重要性（标题、开头更重要）
        position_importance = 0.5
        text_length = len(text)
        for i, _char in enumerate(text):
            if word in text[i: i + len(word)]:
                if i < text_length * 0.1:  # 前10%
                    position_importance = 1.0
                elif i < text_length * 0.3:  # 前30%
                    position_importance = 0.8
                break

        # 上下文重要性（周围是否有其他重要词汇）
        context_importance = 0.5
        if any(fw in text for fw in self.financial_weights.keys()):
            context_importance = 0.8

        return (freq_importance + position_importance + context_importance) / 3


class EntityExtractor:
    """实体提取器"""

    def __init__(self):
        # 实体识别模式
        self.entity_patterns = {
            "company": [
                r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*(?:公司|集团|股份|有限)",
                r"([^\s，。,.\d]{2,8})\s*(?:公司|集团|股份)",
                r"([A-Z]{2,5})\s*(?:公司|Corp|Inc|Ltd)",
            ],
            "stock_code": [
                r"([0-9]{6})",  # A股代码
                r"([A-Z]{1,5})",  # 美股代码
                r"(\d{5}\.HK)",  # 港股代码
            ],
            "money": [
                r"(\d+(?:\.\d+)?)\s*(?:亿|万|千万)\s*(?:元|美元|港元)",
                r"([￥$]\s*\d+(?:,\d{3})*(?:\.\d{2})?)",
            ],
            "percentage": [
                r"(\d+(?:\.\d+)?)\s*%",
            ],
            "date": [
                r"(\d{4}年\d{1,2}月\d{1,2}日)",
                r"(\d{4}-\d{2}-\d{2})",
                r"(\d{1,2}月\d{1,2}日)",
            ],
            "person": [
                r"([A-Z][a-z]+\s+[A-Z][a-z]+)",  # 英文人名
                r"([\u4e00-\u9fff]{2,4}(?:先生|女士|总裁|CEO|董事长|经理))",  # 中文人名+职位
            ],
        }

    def extract_entities(self, text: str) -> dict[str, list[EntityResult]]:
        """
        提取实体

        Args:
            text: 输入文本

        Returns:
            按实体类型分组的实体列表
        """
        entities = {entity_type: [] for entity_type in self.entity_patterns.keys()}

        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    entity_text = match.group(1) if match.groups() else match.group(0)

                    # 计算置信度
                    confidence = self._calculate_entity_confidence(
                        entity_text, entity_type, text
                    )

                    if confidence >= 0.3:  # 置信度阈值
                        entities[entity_type].append(
                            EntityResult(
                                entity=entity_text,
                                entity_type=entity_type,
                                positions=[match.start()],
                                confidence=confidence,
                            )
                        )

        # 去重和合并
        for entity_type in entities:
            entities[entity_type] = self._deduplicate_entities(entities[entity_type])

        return entities

    def _calculate_entity_confidence(
        self, entity: str, entity_type: str, text: str
    ) -> float:
        """计算实体识别置信度"""
        base_confidence = 0.5

        # 基于实体长度
        length_bonus = min(0.2, len(entity) / 10)

        # 基于上下文
        context_bonus = 0
        if entity_type == "company":
            if any(word in text for word in ["上市", "股票", "投资", "业绩"]):
                context_bonus = 0.3
        elif entity_type == "money":
            if any(word in text for word in ["收入", "盈利", "营收", "投资"]):
                context_bonus = 0.2

        # 基于格式规范性
        format_bonus = 0
        if entity_type == "stock_code":
            if re.match(r"^\d{6}$", entity) or re.match(r"^[A-Z]{1,5}$", entity):
                format_bonus = 0.3

        total_confidence = base_confidence + length_bonus + context_bonus + format_bonus
        return min(1.0, total_confidence)

    def _deduplicate_entities(self, entities: list[EntityResult]) -> list[EntityResult]:
        """去重合并相似实体"""
        if not entities:
            return []

        # 按实体文本分组
        entity_groups = {}
        for entity in entities:
            key = entity.entity.lower().strip()
            if key not in entity_groups:
                entity_groups[key] = []
            entity_groups[key].append(entity)

        # 每组选择置信度最高的
        deduplicated = []
        for group in entity_groups.values():
            best_entity = max(group, key=lambda x: x.confidence)
            # 合并所有位置
            all_positions = []
            for entity in group:
                all_positions.extend(entity.positions)
            best_entity.positions = sorted(set(all_positions))
            deduplicated.append(best_entity)

        return sorted(deduplicated, key=lambda x: x.confidence, reverse=True)


class TextAnalyzer:
    """文本分析器"""

    def __init__(self):
        self.cleaner = TextCleaner()
        self.keyword_extractor = KeywordExtractor()
        self.entity_extractor = EntityExtractor()

    def analyze_text_features(self, text: str) -> TextFeatures:
        """
        分析文本特征

        Args:
            text: 输入文本

        Returns:
            文本特征
        """
        if not text:
            return TextFeatures(0, 0, 0, 0, 0.0, 0.0, 0)

        # 清理文本
        cleaned_text = self.cleaner.clean_text(text)

        # 基本统计
        length = len(cleaned_text)
        sentences = re.split(r"[.!?。！？]", cleaned_text)
        sentence_count = len([s for s in sentences if s.strip()])

        # 分词统计
        words = list(jieba.cut(cleaned_text))
        words = [w for w in words if len(w) > 1]  # 过滤单字符
        word_count = len(words)
        unique_words = len(set(words))

        # 平均句长
        avg_sentence_length = length / max(1, sentence_count)

        # 复杂度评分（基于词汇多样性和句子长度）
        complexity_score = self._calculate_complexity(
            unique_words, word_count, avg_sentence_length
        )

        # 金融术语统计
        financial_terms_count = self._count_financial_terms(cleaned_text)

        return TextFeatures(
            length=length,
            sentence_count=sentence_count,
            word_count=word_count,
            unique_words=unique_words,
            avg_sentence_length=round(avg_sentence_length, 2),
            complexity_score=round(complexity_score, 2),
            financial_terms_count=financial_terms_count,
        )

    def _calculate_complexity(
        self, unique_words: int, total_words: int, avg_sentence_length: float
    ) -> float:
        """计算文本复杂度"""
        if total_words == 0:
            return 0.0

        # 词汇多样性
        lexical_diversity = unique_words / total_words

        # 句子长度复杂度
        sentence_complexity = min(1.0, avg_sentence_length / 50)

        # 综合复杂度
        complexity = (lexical_diversity * 0.6 + sentence_complexity * 0.4) * 10

        return min(10.0, complexity)

    def _count_financial_terms(self, text: str) -> int:
        """统计金融术语数量"""
        financial_terms = [
            "股票",
            "股价",
            "股市",
            "上市",
            "投资",
            "收益",
            "盈利",
            "亏损",
            "业绩",
            "财报",
            "涨",
            "跌",
            "暴涨",
            "暴跌",
            "突破",
            "政策",
            "监管",
            "银行",
            "基金",
            "证券",
            "市场",
            "经济",
            "金融",
            "资本",
            "融资",
            "并购",
            "重组",
        ]

        count = 0
        for term in financial_terms:
            count += text.count(term)

        return count

    def extract_key_information(self, text: str) -> dict[str, Any]:
        """
        提取关键信息

        Args:
            text: 输入文本

        Returns:
            包含关键词、实体、特征的综合信息
        """
        # 提取关键词
        keywords = self.keyword_extractor.extract_keywords(text, top_k=15)

        # 提取实体
        entities = self.entity_extractor.extract_entities(text)

        # 分析文本特征
        features = self.analyze_text_features(text)

        # 生成摘要
        summary = self._generate_text_summary(text, keywords, entities, features)

        return {
            "keywords": [
                {
                    "keyword": kw.keyword,
                    "weight": kw.weight,
                    "frequency": kw.frequency,
                    "importance": kw.importance,
                }
                for kw in keywords
            ],
            "entities": {
                entity_type: [
                    {
                        "entity": e.entity,
                        "confidence": e.confidence,
                        "positions": e.positions,
                    }
                    for e in entity_list
                ]
                for entity_type, entity_list in entities.items()
            },
            "features": {
                "length": features.length,
                "sentence_count": features.sentence_count,
                "word_count": features.word_count,
                "unique_words": features.unique_words,
                "avg_sentence_length": features.avg_sentence_length,
                "complexity_score": features.complexity_score,
                "financial_terms_count": features.financial_terms_count,
            },
            "summary": summary,
        }

    def _generate_text_summary(
        self,
        text: str,
        keywords: list[KeywordResult],
        entities: dict[str, list[EntityResult]],
        features: TextFeatures,
    ) -> dict[str, Any]:
        """生成文本摘要信息"""
        # 主要主题（基于关键词）
        main_topics = [kw.keyword for kw in keywords[:5]]

        # 提及的公司
        companies = [e.entity for e in entities.get("company", [])]

        # 重要数据
        money_amounts = [e.entity for e in entities.get("money", [])]
        percentages = [e.entity for e in entities.get("percentage", [])]

        # 文本类型判断
        text_type = "financial_news"  # 简化实现
        if features.financial_terms_count >= 5:
            text_type = "financial_analysis"
        elif any(word in text for word in ["政策", "监管", "法规"]):
            text_type = "policy_news"
        elif any(word in text for word in ["技术", "创新", "研发"]):
            text_type = "technology_news"

        return {
            "main_topics": main_topics,
            "mentioned_companies": companies[:5],
            "key_numbers": {"money_amounts": money_amounts, "percentages": percentages},
            "text_type": text_type,
            "complexity_level": "高"
            if features.complexity_score > 7
            else "中"
            if features.complexity_score > 4
            else "低",
            "financial_relevance": "高"
            if features.financial_terms_count > 10
            else "中"
            if features.financial_terms_count > 3
            else "低",
        }


# 便捷函数
def clean_text(text: str) -> str:
    """便捷的文本清理函数"""
    cleaner = TextCleaner()
    return cleaner.clean_text(text)


def extract_keywords(text: str, top_k: int = 10) -> list[dict[str, Any]]:
    """便捷的关键词提取函数"""
    extractor = KeywordExtractor()
    keywords = extractor.extract_keywords(text, top_k)
    return [
        {
            "keyword": kw.keyword,
            "weight": kw.weight,
            "frequency": kw.frequency,
            "importance": kw.importance,
        }
        for kw in keywords
    ]


def extract_entities(text: str) -> dict[str, list[str]]:
    """便捷的实体提取函数"""
    extractor = EntityExtractor()
    entities = extractor.extract_entities(text)
    return {
        entity_type: [e.entity for e in entity_list]
        for entity_type, entity_list in entities.items()
    }


def analyze_text(text: str) -> dict[str, Any]:
    """便捷的文本分析函数"""
    analyzer = TextAnalyzer()
    return analyzer.extract_key_information(text)
