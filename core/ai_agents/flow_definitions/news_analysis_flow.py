#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
新闻分析工作流

基于PocketFlow框架的新闻分析四层处理流水线：
1. 规则预筛选层 - 基于关键词和规则的快速筛选
2. AI深度分析层 - 调用千问LLM进行深度分析
3. 情感评估层 - 情感分析和市场影响评估
4. 投资建议层 - 生成投资建议和风险评估
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pocketflow import AsyncFlow, AsyncNode

from ..llm_clients.qwen_client import QwenLLMClient

logger = logging.getLogger(__name__)

class PrefilterNode(AsyncNode):
    """
    规则预筛选节点
    基于关键词、新闻源权重、时效性进行快速筛选
    """
    
    def __init__(self):
        super().__init__()
        # 投资相关关键词
        self.investment_keywords = {
            "positive": ["上涨", "增长", "突破", "利好", "收购", "合作", "创新", "盈利"],
            "negative": ["下跌", "暴跌", "亏损", "风险", "警告", "危机", "裁员", "退市"],
            "sectors": ["科技", "医疗", "金融", "地产", "新能源", "消费", "制造", "互联网"]
        }
        
        # 新闻源权重（1-10，数字越大权重越高）
        self.source_weights = {
            "新华社": 9, "人民日报": 9, "央视": 8,
            "第一财经": 8, "财新": 8, "21世纪经济报道": 7,
            "东方财富": 6, "雪球": 5, "其他": 3
        }
    
    async def run_async(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        预筛选处理逻辑
        
        Args:
            data: 包含articles列表的输入数据
            
        Returns:
            筛选后的文章和评分
        """
        articles = data.get("articles", [])
        filtered_articles = []
        
        for article in articles:
            score = self._calculate_relevance_score(article)
            
            # 只保留评分大于阈值的文章
            if score >= 3.0:
                article["relevance_score"] = score
                filtered_articles.append(article)
                logger.debug(f"文章通过预筛选: {article.get('title', '')} (评分: {score})")
        
        logger.info(f"预筛选完成: {len(articles)} -> {len(filtered_articles)} 篇文章")
        
        return {
            "filtered_articles": filtered_articles,
            "original_count": len(articles),
            "filtered_count": len(filtered_articles),
            "filter_ratio": len(filtered_articles) / len(articles) if articles else 0,
            **data  # 保留原始数据
        }
    
    def _calculate_relevance_score(self, article: Dict[str, Any]) -> float:
        """计算文章相关性评分"""
        score = 0.0
        title = article.get("title", "")
        content = article.get("content", "")
        source = article.get("source_name", "其他")
        
        # 关键词评分
        text = f"{title} {content}".lower()
        
        # 正面关键词
        positive_count = sum(1 for kw in self.investment_keywords["positive"] if kw in text)
        score += positive_count * 0.5
        
        # 负面关键词
        negative_count = sum(1 for kw in self.investment_keywords["negative"] if kw in text)
        score += negative_count * 0.5
        
        # 行业关键词
        sector_count = sum(1 for kw in self.investment_keywords["sectors"] if kw in text)
        score += sector_count * 0.3
        
        # 新闻源权重
        source_weight = self.source_weights.get(source, 3) / 10.0
        score *= (1 + source_weight)
        
        # 时效性评分（假设有publish_time字段）
        publish_time = article.get("publish_time")
        if publish_time:
            # 简单时效性评分逻辑
            score *= 1.2  # 有发布时间的文章加分
        
        return min(score, 10.0)  # 限制最大评分

class AIAnalysisNode(AsyncNode):
    """
    AI深度分析节点
    调用千问LLM进行文章深度分析
    """
    
    def __init__(self, qwen_client: Optional[QwenLLMClient] = None):
        super().__init__()
        self.qwen_client = qwen_client
    
    async def run_async(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI分析处理逻辑
        
        Args:
            data: 包含filtered_articles的数据
            
        Returns:
            AI分析结果
        """
        articles = data.get("filtered_articles", [])
        
        if not articles:
            return {
                **data,
                "ai_analysis_results": [], 
                "analysis_count": 0
            }
        
        # 使用千问客户端进行批量分析
        if not self.qwen_client:
            # 模拟分析结果
            results = await self._mock_analyze(articles)
        else:
            # 真实AI分析
            results = await self._batch_analyze(self.qwen_client, articles)
        
        logger.info(f"AI分析完成: {len(results)} 篇文章")
        
        return {
            **data,
            "ai_analysis_results": results,
            "analysis_count": len(results),
            "input_articles": articles
        }
    
    async def _mock_analyze(self, articles: List[Dict]) -> List[Dict]:
        """模拟分析结果"""
        results = []
        for i, article in enumerate(articles, 1):
            # 基于文章标题简单分析
            title = article.get("title", "").lower()
            
            # 简单的情感判断
            if any(word in title for word in ["上涨", "增长", "利好", "创新"]):
                sentiment = "positive"
                market_impact = "medium"
                relevance = 7
            elif any(word in title for word in ["下跌", "危机", "风险", "亏损"]):
                sentiment = "negative"
                market_impact = "medium"
                relevance = 6
            else:
                sentiment = "neutral"
                market_impact = "low"
                relevance = 5
            
            results.append({
                "article_index": i,
                "summary": article.get("title", ""),
                "key_points": [f"关键点{i}"],
                "sentiment": sentiment,
                "market_impact": market_impact,
                "affected_sectors": ["金融", "科技"],
                "investment_relevance": relevance
            })
        
        return results
    
    async def _batch_analyze(self, client: QwenLLMClient, articles: List[Dict]) -> List[Dict]:
        """真实AI批量分析文章"""
        # 构建分析提示词
        analysis_prompt = """
请分析以下新闻文章的投资价值：

{articles}

对每篇文章进行分析，返回JSON格式：
{{
  "analyses": [
    {{
      "article_index": 1,
      "summary": "文章摘要",
      "key_points": ["要点1", "要点2"],
      "sentiment": "positive/neutral/negative",
      "market_impact": "high/medium/low",
      "affected_sectors": ["行业1", "行业2"],
      "investment_relevance": 1-10
    }}
  ]
}}
"""
        
        # 格式化文章文本
        articles_text = ""
        for i, article in enumerate(articles, 1):
            title = article.get("title", "无标题")
            content = article.get("content", "")[:300]  # 限制内容长度
            articles_text += f"{i}. {title}\n{content}\n\n"
        
        try:
            # 调用千问API
            response = await client.chat_completion([
                {"role": "user", "content": analysis_prompt.format(articles=articles_text)}
            ], temperature=0.3)
            
            # 解析JSON响应
            analysis_result = json.loads(response.content)
            return analysis_result.get("analyses", [])
            
        except Exception as e:
            logger.error(f"AI分析失败: {e}")
            # 返回模拟结果作为备用
            return await self._mock_analyze(articles)

class SentimentAnalysisNode(AsyncNode):
    """
    情感评估节点
    基于AI分析结果进行情感量化和市场影响评估
    """
    
    async def run_async(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        情感评估处理逻辑
        
        Args:
            data: 包含ai_analysis_results的数据
            
        Returns:
            情感评估结果
        """
        analyses = data.get("ai_analysis_results", [])
        sentiment_results = []
        
        for analysis in analyses:
            sentiment_score = self._calculate_sentiment_score(analysis)
            market_impact_score = self._calculate_market_impact(analysis)
            
            sentiment_result = {
                "article_index": analysis.get("article_index"),
                "sentiment_score": sentiment_score,  # -10 到 10
                "market_impact_score": market_impact_score,  # 0 到 10
                "sentiment_label": self._get_sentiment_label(sentiment_score),
                "impact_label": analysis.get("market_impact", "low"),
                "confidence": self._calculate_confidence(analysis)
            }
            
            sentiment_results.append(sentiment_result)
        
        # 计算整体情感
        overall_sentiment = self._calculate_overall_sentiment(sentiment_results)
        
        logger.info(f"情感评估完成: {len(sentiment_results)} 篇文章，整体情感: {overall_sentiment}")
        
        return {
            **data,
            "sentiment_results": sentiment_results,
            "overall_sentiment": overall_sentiment,
            "ai_analysis_results": analyses
        }
    
    def _calculate_sentiment_score(self, analysis: Dict) -> float:
        """计算情感评分"""
        sentiment = analysis.get("sentiment", "neutral").lower()
        relevance = analysis.get("investment_relevance", 5)
        
        # 基础情感评分
        base_scores = {"positive": 6, "neutral": 0, "negative": -6}
        base_score = base_scores.get(sentiment, 0)
        
        # 根据投资相关性调整
        adjusted_score = base_score * (relevance / 5.0)
        
        return max(-10, min(10, adjusted_score))
    
    def _calculate_market_impact(self, analysis: Dict) -> float:
        """计算市场影响评分"""
        impact = analysis.get("market_impact", "low").lower()
        relevance = analysis.get("investment_relevance", 5)
        
        # 基础影响评分
        base_scores = {"high": 8, "medium": 5, "low": 2}
        base_score = base_scores.get(impact, 2)
        
        # 根据投资相关性调整
        adjusted_score = base_score * (relevance / 5.0)
        
        return max(0, min(10, adjusted_score))
    
    def _get_sentiment_label(self, score: float) -> str:
        """获取情感标签"""
        if score > 3:
            return "积极"
        elif score < -3:
            return "消极"
        else:
            return "中性"
    
    def _calculate_confidence(self, analysis: Dict) -> float:
        """计算置信度"""
        relevance = analysis.get("investment_relevance", 5)
        has_key_points = len(analysis.get("key_points", [])) > 0
        has_sectors = len(analysis.get("affected_sectors", [])) > 0
        
        confidence = relevance / 10.0
        if has_key_points:
            confidence += 0.1
        if has_sectors:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _calculate_overall_sentiment(self, sentiment_results: List[Dict]) -> Dict[str, Any]:
        """计算整体市场情感"""
        if not sentiment_results:
            return {"score": 0, "label": "中性", "confidence": 0}
        
        # 加权平均（根据置信度）
        total_weight = sum(r["confidence"] for r in sentiment_results)
        if total_weight == 0:
            weighted_score = 0
        else:
            weighted_score = sum(
                r["sentiment_score"] * r["confidence"] 
                for r in sentiment_results
            ) / total_weight
        
        return {
            "score": round(weighted_score, 2),
            "label": self._get_sentiment_label(weighted_score),
            "confidence": total_weight / len(sentiment_results),
            "article_count": len(sentiment_results)
        }

class InvestmentAdviceNode(AsyncNode):
    """
    投资建议节点
    基于情感分析结果生成投资建议和风险评估
    """
    
    async def run_async(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        投资建议处理逻辑
        
        Args:
            data: 包含sentiment_results的数据
            
        Returns:
            投资建议结果
        """
        sentiment_results = data.get("sentiment_results", [])
        overall_sentiment = data.get("overall_sentiment", {})
        
        # 生成投资建议
        investment_advice = self._generate_investment_advice(overall_sentiment)
        
        # 生成风险评估
        risk_assessment = self._generate_risk_assessment(sentiment_results)
        
        # 生成行业建议
        sector_recommendations = self._generate_sector_recommendations(
            data.get("ai_analysis_results", [])
        )
        
        logger.info(f"投资建议生成完成: {investment_advice['action']}")
        
        return {
            "investment_advice": investment_advice,
            "risk_assessment": risk_assessment,
            "sector_recommendations": sector_recommendations,
            "analysis_summary": {
                "total_articles": len(sentiment_results),
                "overall_sentiment": overall_sentiment,
                "generation_time": datetime.now().isoformat()
            }
        }
    
    def _generate_investment_advice(self, overall_sentiment: Dict) -> Dict[str, Any]:
        """生成投资建议"""
        score = overall_sentiment.get("score", 0)
        confidence = overall_sentiment.get("confidence", 0)
        
        # 基于情感评分和置信度生成建议
        if score > 5 and confidence > 0.7:
            action = "买入"
            reason = "市场情感积极，投资机会良好"
        elif score > 2 and confidence > 0.5:
            action = "关注"
            reason = "市场情感偏积极，可考虑逐步建仓"
        elif score < -5 and confidence > 0.7:
            action = "减仓"
            reason = "市场情感消极，建议降低风险敞口"
        elif score < -2 and confidence > 0.5:
            action = "谨慎"
            reason = "市场情感偏消极，建议观望"
        else:
            action = "持有"
            reason = "市场情感中性或信息不足，维持现状"
        
        return {
            "action": action,
            "reason": reason,
            "confidence_level": confidence,
            "time_horizon": "短期" if confidence > 0.8 else "中期",
            "position_size": self._calculate_position_size(score, confidence)
        }
    
    def _generate_risk_assessment(self, sentiment_results: List[Dict]) -> Dict[str, Any]:
        """生成风险评估"""
        if not sentiment_results:
            return {"level": "中", "factors": ["信息不足"], "score": 5}
        
        # 计算风险因子
        volatility = self._calculate_volatility(sentiment_results)
        negative_ratio = len([r for r in sentiment_results if r["sentiment_score"] < 0]) / len(sentiment_results)
        low_confidence_ratio = len([r for r in sentiment_results if r["confidence"] < 0.5]) / len(sentiment_results)
        
        risk_score = volatility * 3 + negative_ratio * 4 + low_confidence_ratio * 3
        
        if risk_score > 7:
            level = "高"
            factors = ["市场情感波动大", "负面消息较多", "信息可靠性低"]
        elif risk_score > 4:
            level = "中"
            factors = ["市场情感一般", "存在一定不确定性"]
        else:
            level = "低"
            factors = ["市场情感稳定", "信息相对可靠"]
        
        return {
            "level": level,
            "score": round(risk_score, 2),
            "factors": factors,
            "volatility": volatility,
            "negative_ratio": negative_ratio
        }
    
    def _generate_sector_recommendations(self, analyses: List[Dict]) -> List[Dict[str, Any]]:
        """生成行业建议"""
        sector_stats = {}
        
        for analysis in analyses:
            sectors = analysis.get("affected_sectors", [])
            sentiment = analysis.get("sentiment", "neutral")
            relevance = analysis.get("investment_relevance", 5)
            
            for sector in sectors:
                if sector not in sector_stats:
                    sector_stats[sector] = {"positive": 0, "negative": 0, "total": 0, "relevance_sum": 0}
                
                sector_stats[sector]["total"] += 1
                sector_stats[sector]["relevance_sum"] += relevance
                
                if sentiment == "positive":
                    sector_stats[sector]["positive"] += 1
                elif sentiment == "negative":
                    sector_stats[sector]["negative"] += 1
        
        # 生成行业建议
        recommendations = []
        for sector, stats in sector_stats.items():
            if stats["total"] == 0:
                continue
                
            positive_ratio = stats["positive"] / stats["total"]
            avg_relevance = stats["relevance_sum"] / stats["total"]
            
            if positive_ratio > 0.6 and avg_relevance > 6:
                recommendation = "看好"
            elif positive_ratio > 0.4 and avg_relevance > 4:
                recommendation = "中性"
            else:
                recommendation = "谨慎"
            
            recommendations.append({
                "sector": sector,
                "recommendation": recommendation,
                "positive_ratio": positive_ratio,
                "avg_relevance": avg_relevance,
                "mention_count": stats["total"]
            })
        
        # 按相关性和提及次数排序
        recommendations.sort(key=lambda x: (x["avg_relevance"], x["mention_count"]), reverse=True)
        
        return recommendations[:5]  # 返回前5个行业
    
    def _calculate_position_size(self, score: float, confidence: float) -> str:
        """计算建议仓位大小"""
        if abs(score) > 6 and confidence > 0.8:
            return "大仓位"
        elif abs(score) > 3 and confidence > 0.6:
            return "中仓位"
        else:
            return "小仓位"
    
    def _calculate_volatility(self, sentiment_results: List[Dict]) -> float:
        """计算情感波动性"""
        scores = [r["sentiment_score"] for r in sentiment_results]
        if len(scores) < 2:
            return 0
        
        avg_score = sum(scores) / len(scores)
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        volatility = variance ** 0.5 / 10  # 标准化到0-1
        
        return min(1.0, volatility)

class NewsAnalysisFlow:
    """
    新闻分析主工作流
    使用PocketFlow实现四层处理流水线
    """
    
    def __init__(self, qwen_client: Optional[QwenLLMClient] = None):
        # 创建处理节点
        self.prefilter = PrefilterNode()
        self.ai_analysis = AIAnalysisNode(qwen_client)
        self.sentiment_analysis = SentimentAnalysisNode()
        self.investment_advice = InvestmentAdviceNode()
    
    async def analyze_news(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析新闻文章
        
        Args:
            articles: 新闻文章列表
            
        Returns:
            完整的分析结果
        """
        logger.info(f"开始新闻分析工作流，输入文章数: {len(articles)}")
        
        # 创建PocketFlow流水线
        flow = AsyncFlow(start=self.prefilter)
        flow = flow.next(self.ai_analysis)
        flow = flow.next(self.sentiment_analysis)
        flow = flow.next(self.investment_advice)
        
        # 执行工作流
        input_data = {"articles": articles}
        result = await flow.run_async(input_data)
        
        logger.info("新闻分析工作流完成")
        return result

# 便捷接口
async def analyze_news_articles(
    articles: List[Dict[str, Any]], 
    qwen_client: Optional[QwenLLMClient] = None
) -> Dict[str, Any]:
    """
    便捷的新闻分析接口
    
    Args:
        articles: 新闻文章列表
        qwen_client: 可选的千问客户端
        
    Returns:
        分析结果
    """
    flow = NewsAnalysisFlow(qwen_client)
    return await flow.analyze_news(articles) 