#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
情感分析器

专业的金融文本情感分析工具，支持：
- 基于词典的快速情感分析
- 上下文感知的深度情感分析
- 多维度情感评分和置信度计算
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SentimentResult:
    """情感分析结果"""
    score: float  # -10 到 +10
    label: str   # 情感标签
    confidence: float  # 置信度 0-1
    dominant_emotion: str  # 主导情感
    key_phrases: List[str]  # 关键短语
    breakdown: Dict[str, Any]  # 详细分解

class FinancialSentimentDictionary:
    """金融情感词典"""
    
    def __init__(self):
        self.sentiment_dict = {
            "positive": {
                "strong": {
                    "words": ["暴涨", "大涨", "飞涨", "暴升", "爆发", "突破", "创新高", "翻倍", "井喷"],
                    "weight": 3.0
                },
                "medium": {
                    "words": ["上涨", "上升", "增长", "攀升", "走强", "反弹", "好转", "改善", "回升"],
                    "weight": 2.0
                },
                "weak": {
                    "words": ["微涨", "小涨", "略涨", "企稳", "向好", "乐观", "正面", "利好", "稳健"],
                    "weight": 1.0
                }
            },
            "negative": {
                "strong": {
                    "words": ["暴跌", "大跌", "跌停", "崩盘", "血洗", "重挫", "腰斩", "雪崩", "溃败"],
                    "weight": 3.0
                },
                "medium": {
                    "words": ["下跌", "下降", "下滑", "走弱", "回调", "调整", "疲软", "不振", "承压"],
                    "weight": 2.0
                },
                "weak": {
                    "words": ["微跌", "小跌", "略跌", "震荡", "谨慎", "担忧", "风险", "压力", "不确定"],
                    "weight": 1.0
                }
            },
            "neutral": {
                "words": ["平稳", "持平", "横盘", "整理", "观望", "等待", "关注", "监控", "维持"],
                "weight": 0.0
            }
        }
        
        # 否定词
        self.negation_words = ["不", "未", "没", "非", "无", "否", "别", "勿", "非但不", "绝不"]
        
        # 程度副词
        self.intensity_modifiers = {
            "very_strong": {"words": ["极其", "非常", "十分", "特别", "相当"], "multiplier": 1.5},
            "strong": {"words": ["很", "较", "比较", "更加"], "multiplier": 1.2},
            "weak": {"words": ["有点", "稍微", "略微", "稍"], "multiplier": 0.8}
        }

class SentimentAnalyzer:
    """情感分析器主类"""
    
    def __init__(self, llm_client=None):
        self.dictionary = FinancialSentimentDictionary()
        self.llm_client = llm_client
    
    def analyze_text(self, text: str, use_llm: bool = False) -> SentimentResult:
        """
        分析文本情感
        
        Args:
            text: 待分析文本
            use_llm: 是否使用LLM进行深度分析
            
        Returns:
            情感分析结果
        """
        if not text or not text.strip():
            return SentimentResult(
                score=0.0, label="中性", confidence=0.0,
                dominant_emotion="neutral", key_phrases=[], breakdown={}
            )
        
        # 基础词典分析
        basic_result = self._analyze_with_dictionary(text)
        
        if use_llm and self.llm_client:
            # LLM深度分析
            enhanced_result = self._enhance_with_llm(text, basic_result)
            return enhanced_result
        else:
            return basic_result
    
    def _analyze_with_dictionary(self, text: str) -> SentimentResult:
        """基于词典的情感分析"""
        
        # 预处理文本
        clean_text = self._preprocess_text(text)
        
        # 检测情感词汇
        sentiment_matches = self._detect_sentiment_words(clean_text)
        
        # 计算基础评分
        base_score = self._calculate_base_score(sentiment_matches, clean_text)
        
        # 应用上下文调整
        adjusted_score = self._apply_context_adjustments(base_score, clean_text, sentiment_matches)
        
        # 提取关键短语
        key_phrases = self._extract_sentiment_phrases(clean_text, sentiment_matches)
        
        # 计算置信度
        confidence = self._calculate_confidence(sentiment_matches, clean_text)
        
        # 获取主导情感
        dominant_emotion = self._get_dominant_emotion(sentiment_matches)
        
        # 获取情感标签
        label = self._get_sentiment_label(adjusted_score)
        
        # 构建详细分解
        breakdown = {
            "base_score": base_score,
            "adjusted_score": adjusted_score,
            "sentiment_matches": sentiment_matches,
            "word_count": len(clean_text),
            "key_sentiment_words": self._get_key_words(sentiment_matches)
        }
        
        return SentimentResult(
            score=round(adjusted_score, 2),
            label=label,
            confidence=round(confidence, 2),
            dominant_emotion=dominant_emotion,
            key_phrases=key_phrases,
            breakdown=breakdown
        )
    
    def _preprocess_text(self, text: str) -> str:
        """预处理文本"""
        # 移除URL、邮箱等
        text = re.sub(r'http[s]?://\S+', '', text)
        text = re.sub(r'\S+@\S+', '', text)
        
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _detect_sentiment_words(self, text: str) -> Dict[str, Any]:
        """检测情感词汇"""
        matches = {
            "positive": {"strong": [], "medium": [], "weak": []},
            "negative": {"strong": [], "medium": [], "weak": []},
            "neutral": []
        }
        
        # 检测正面和负面情感词
        for sentiment_type in ["positive", "negative"]:
            for intensity in ["strong", "medium", "weak"]:
                words = self.dictionary.sentiment_dict[sentiment_type][intensity]["words"]
                for word in words:
                    if word in text:
                        # 记录词汇及其位置
                        positions = [m.start() for m in re.finditer(re.escape(word), text)]
                        for pos in positions:
                            matches[sentiment_type][intensity].append({
                                "word": word,
                                "position": pos,
                                "has_negation": self._check_negation(text, pos),
                                "intensity_modifier": self._check_intensity_modifier(text, pos)
                            })
        
        # 检测中性词
        for word in self.dictionary.sentiment_dict["neutral"]["words"]:
            if word in text:
                positions = [m.start() for m in re.finditer(re.escape(word), text)]
                for pos in positions:
                    matches["neutral"].append({
                        "word": word,
                        "position": pos
                    })
        
        return matches
    
    def _check_negation(self, text: str, word_position: int) -> bool:
        """检查否定词"""
        # 检查词汇前10个字符内是否有否定词
        start = max(0, word_position - 10)
        prefix = text[start:word_position]
        
        return any(neg_word in prefix for neg_word in self.dictionary.negation_words)
    
    def _check_intensity_modifier(self, text: str, word_position: int) -> float:
        """检查程度副词"""
        # 检查词汇前8个字符内的程度副词
        start = max(0, word_position - 8)
        prefix = text[start:word_position]
        
        for intensity_level, info in self.dictionary.intensity_modifiers.items():
            for modifier in info["words"]:
                if modifier in prefix:
                    return info["multiplier"]
        
        return 1.0  # 无修饰词
    
    def _calculate_base_score(self, sentiment_matches: Dict, text: str) -> float:
        """计算基础情感评分"""
        positive_score = 0.0
        negative_score = 0.0
        
        # 计算正面评分
        for intensity, matches in sentiment_matches["positive"].items():
            base_weight = self.dictionary.sentiment_dict["positive"][intensity]["weight"]
            for match in matches:
                weight = base_weight
                
                # 应用程度副词调整
                weight *= match.get("intensity_modifier", 1.0)
                
                # 应用否定词调整
                if match.get("has_negation", False):
                    negative_score += weight  # 否定的正面词变成负面
                else:
                    positive_score += weight
        
        # 计算负面评分
        for intensity, matches in sentiment_matches["negative"].items():
            base_weight = self.dictionary.sentiment_dict["negative"][intensity]["weight"]
            for match in matches:
                weight = base_weight
                
                # 应用程度副词调整
                weight *= match.get("intensity_modifier", 1.0)
                
                # 应用否定词调整
                if match.get("has_negation", False):
                    positive_score += weight  # 否定的负面词变成正面
                else:
                    negative_score += weight
        
        # 计算净评分
        net_score = positive_score - negative_score
        
        # 标准化到-10到+10范围
        return max(-10, min(10, net_score))
    
    def _apply_context_adjustments(self, base_score: float, text: str, matches: Dict) -> float:
        """应用上下文调整"""
        adjusted_score = base_score
        
        # 文本长度调整
        text_length = len(text)
        if text_length < 50:
            # 短文本情感强度增强
            adjusted_score *= 1.1
        elif text_length > 500:
            # 长文本情感强度削弱
            adjusted_score *= 0.9
        
        # 情感词密度调整
        total_sentiment_words = (
            sum(len(matches["positive"][intensity]) for intensity in ["strong", "medium", "weak"]) +
            sum(len(matches["negative"][intensity]) for intensity in ["strong", "medium", "weak"])
        )
        
        if total_sentiment_words > 0:
            density = total_sentiment_words / max(1, text_length / 10)  # 每10个字符的情感词数
            if density > 2:
                # 高密度增强情感
                adjusted_score *= 1.2
            elif density < 0.5:
                # 低密度削弱情感
                adjusted_score *= 0.8
        
        # 确保在合理范围内
        return max(-10, min(10, adjusted_score))
    
    def _extract_sentiment_phrases(self, text: str, matches: Dict) -> List[str]:
        """提取情感短语"""
        phrases = []
        
        # 收集所有情感词的位置
        all_positions = []
        
        for sentiment_type in ["positive", "negative"]:
            for intensity_matches in matches[sentiment_type].values():
                for match in intensity_matches:
                    all_positions.append((match["position"], match["word"]))
        
        for match in matches["neutral"]:
            all_positions.append((match["position"], match["word"]))
        
        # 为每个情感词提取上下文短语
        for position, word in all_positions:
            phrase = self._extract_phrase_context(text, position, word)
            if phrase and phrase not in phrases:
                phrases.append(phrase)
        
        return phrases[:5]  # 限制数量
    
    def _extract_phrase_context(self, text: str, position: int, word: str, context_length: int = 25) -> str:
        """提取词汇上下文短语"""
        start = max(0, position - context_length)
        end = min(len(text), position + len(word) + context_length)
        
        phrase = text[start:end].strip()
        
        # 确保短语完整
        if start > 0:
            phrase = "..." + phrase
        if end < len(text):
            phrase = phrase + "..."
        
        return phrase
    
    def _calculate_confidence(self, matches: Dict, text: str) -> float:
        """计算分析置信度"""
        # 基于情感词数量
        total_words = (
            sum(len(matches["positive"][intensity]) for intensity in ["strong", "medium", "weak"]) +
            sum(len(matches["negative"][intensity]) for intensity in ["strong", "medium", "weak"]) +
            len(matches["neutral"])
        )
        
        # 基于文本长度
        text_length = len(text)
        
        # 基础置信度
        if total_words >= 5:
            base_confidence = 0.9
        elif total_words >= 3:
            base_confidence = 0.7
        elif total_words >= 1:
            base_confidence = 0.5
        else:
            base_confidence = 0.2
        
        # 文本长度调整
        if text_length > 100:
            length_bonus = min(0.1, (text_length - 100) / 1000)
            base_confidence += length_bonus
        
        # 情感词密度调整
        if total_words > 0 and text_length > 0:
            density = total_words / (text_length / 50)  # 每50字符的情感词数
            if density > 1:
                base_confidence += min(0.1, (density - 1) * 0.05)
        
        return min(1.0, base_confidence)
    
    def _get_dominant_emotion(self, matches: Dict) -> str:
        """获取主导情感类型"""
        positive_count = sum(len(matches["positive"][intensity]) for intensity in ["strong", "medium", "weak"])
        negative_count = sum(len(matches["negative"][intensity]) for intensity in ["strong", "medium", "weak"])
        neutral_count = len(matches["neutral"])
        
        if positive_count > negative_count and positive_count > neutral_count:
            return "positive"
        elif negative_count > positive_count and negative_count > neutral_count:
            return "negative"
        else:
            return "neutral"
    
    def _get_sentiment_label(self, score: float) -> str:
        """获取情感标签"""
        if score > 6:
            return "极度积极"
        elif score > 3:
            return "积极"
        elif score > 1:
            return "轻微积极"
        elif score > -1:
            return "中性"
        elif score > -3:
            return "轻微消极"
        elif score > -6:
            return "消极"
        else:
            return "极度消极"
    
    def _get_key_words(self, matches: Dict) -> List[str]:
        """获取关键情感词"""
        key_words = []
        
        # 收集强度最高的词汇
        for sentiment_type in ["positive", "negative"]:
            for intensity in ["strong", "medium", "weak"]:
                words = [match["word"] for match in matches[sentiment_type][intensity]]
                key_words.extend(words)
                if len(key_words) >= 10:  # 限制数量
                    break
            if len(key_words) >= 10:
                break
        
        return list(set(key_words))[:10]
    
    async def _enhance_with_llm(self, text: str, basic_result: SentimentResult) -> SentimentResult:
        """使用LLM增强分析结果"""
        # TODO: 实现LLM增强分析
        # 可以调用千问LLM进行更深度的语义理解
        
        # 暂时返回基础结果
        return basic_result
    
    def analyze_batch(self, texts: List[str], use_llm: bool = False) -> List[SentimentResult]:
        """批量分析文本情感"""
        results = []
        
        for text in texts:
            try:
                result = self.analyze_text(text, use_llm)
                results.append(result)
            except Exception as e:
                logger.error(f"情感分析失败: {e}")
                # 返回默认结果
                results.append(SentimentResult(
                    score=0.0, label="分析失败", confidence=0.0,
                    dominant_emotion="unknown", key_phrases=[], breakdown={}
                ))
        
        return results
    
    def get_sentiment_summary(self, results: List[SentimentResult]) -> Dict[str, Any]:
        """生成情感分析摘要"""
        if not results:
            return {}
        
        # 计算平均评分
        valid_results = [r for r in results if r.score != 0 or r.label != "分析失败"]
        if not valid_results:
            return {"error": "没有有效的分析结果"}
        
        avg_score = sum(r.score for r in valid_results) / len(valid_results)
        avg_confidence = sum(r.confidence for r in valid_results) / len(valid_results)
        
        # 统计情感分布
        label_counts = {}
        emotion_counts = {}
        
        for result in valid_results:
            label = result.label
            emotion = result.dominant_emotion
            
            label_counts[label] = label_counts.get(label, 0) + 1
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # 收集所有关键短语
        all_phrases = []
        for result in valid_results:
            all_phrases.extend(result.key_phrases)
        
        # 短语频次统计
        phrase_counts = {}
        for phrase in all_phrases:
            phrase_counts[phrase] = phrase_counts.get(phrase, 0) + 1
        
        top_phrases = sorted(phrase_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_analyzed": len(results),
            "valid_results": len(valid_results),
            "average_sentiment_score": round(avg_score, 2),
            "average_confidence": round(avg_confidence, 2),
            "overall_sentiment": self._get_sentiment_label(avg_score),
            "sentiment_distribution": label_counts,
            "emotion_distribution": emotion_counts,
            "top_sentiment_phrases": [phrase for phrase, count in top_phrases],
            "strongest_sentiment": max(valid_results, key=lambda x: abs(x.score)),
            "highest_confidence": max(valid_results, key=lambda x: x.confidence)
        }

# 便捷函数
def analyze_sentiment(text: str, use_llm: bool = False, llm_client=None) -> SentimentResult:
    """便捷的情感分析函数"""
    analyzer = SentimentAnalyzer(llm_client)
    return analyzer.analyze_text(text, use_llm)

def analyze_sentiment_batch(texts: List[str], use_llm: bool = False, llm_client=None) -> List[SentimentResult]:
    """便捷的批量情感分析函数"""
    analyzer = SentimentAnalyzer(llm_client)
    return analyzer.analyze_batch(texts, use_llm) 