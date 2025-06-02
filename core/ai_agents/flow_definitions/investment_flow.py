#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
投资建议专用工作流

基于PocketFlow框架的投资建议生成流水线：
1. 投资机会识别 - 基于情感和新闻内容识别投资机会
2. 风险评估分析 - 多维度风险因素分析和评估
3. 股票关联分析 - 分析新闻与股票的关联度
4. 投资建议生成 - 综合生成投资建议和操作策略
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pocketflow import AsyncFlow, AsyncNode

logger = logging.getLogger(__name__)

class InvestmentOpportunityNode(AsyncNode):
    """
    投资机会识别节点
    基于情感分析结果和新闻内容识别潜在的投资机会
    """
    
    def __init__(self):
        super().__init__()
        # 投资机会关键词
        self.opportunity_keywords = {
            "policy_support": ["政策", "支持", "扶持", "减税", "补贴", "优惠", "鼓励"],
            "market_expansion": ["扩张", "增长", "需求", "订单", "合同", "业务", "拓展"],
            "technology_breakthrough": ["突破", "创新", "技术", "研发", "专利", "升级"],
            "financial_improvement": ["盈利", "收入", "营收", "业绩", "增长", "回升"],
            "strategic_cooperation": ["合作", "联盟", "并购", "重组", "投资", "合资"],
            "industry_trends": ["趋势", "热点", "概念", "风口", "机遇", "前景"]
        }
        
        # 行业关键词映射
        self.industry_keywords = {
            "technology": ["科技", "互联网", "人工智能", "AI", "芯片", "半导体", "软件"],
            "healthcare": ["医疗", "医药", "生物", "疫苗", "药品", "医院", "健康"],
            "finance": ["银行", "保险", "证券", "金融", "支付", "理财", "信贷"],
            "energy": ["能源", "电力", "新能源", "光伏", "风电", "电池", "储能"],
            "consumer": ["消费", "零售", "电商", "品牌", "食品", "饮料", "服装"],
            "manufacturing": ["制造", "工业", "机械", "汽车", "钢铁", "化工", "材料"],
            "real_estate": ["地产", "房地产", "建筑", "建设", "基建", "装修", "物业"]
        }
    
    async def run_async(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        投资机会识别逻辑
        
        Args:
            data: 包含sentiment analysis结果的数据
            
        Returns:
            投资机会识别结果
        """
        articles = data.get("processed_articles", [])
        sentiment_results = data.get("integrated_sentiment_results", [])
        
        opportunities = []
        
        for article, sentiment in zip(articles, sentiment_results):
            opportunity = self._identify_investment_opportunity(article, sentiment)
            opportunities.append(opportunity)
        
        # 排序和筛选高价值机会
        filtered_opportunities = self._filter_high_value_opportunities(opportunities)
        
        logger.info(f"投资机会识别完成: {len(filtered_opportunities)} 个高价值机会")
        
        return {
            **data,
            "investment_opportunities": opportunities,
            "high_value_opportunities": filtered_opportunities,
            "opportunity_count": len(opportunities)
        }
    
    def _identify_investment_opportunity(self, article: Dict, sentiment: Dict) -> Dict[str, Any]:
        """识别单个投资机会"""
        title = article.get("clean_title", "")
        content = article.get("clean_content", "")
        text = f"{title} {content}"
        
        # 识别机会类型
        opportunity_types = self._detect_opportunity_types(text)
        
        # 识别相关行业
        related_industries = self._detect_related_industries(text)
        
        # 计算机会评分
        opportunity_score = self._calculate_opportunity_score(
            sentiment, opportunity_types, related_industries
        )
        
        # 提取关键信息
        key_info = self._extract_key_investment_info(text)
        
        return {
            "article_index": article.get("article_index", 0),
            "opportunity_types": opportunity_types,
            "related_industries": related_industries,
            "opportunity_score": opportunity_score,
            "sentiment_score": sentiment.get("final_sentiment_score", 0),
            "key_information": key_info,
            "time_sensitivity": self._assess_time_sensitivity(text),
            "confidence": self._calculate_confidence(opportunity_types, sentiment)
        }
    
    def _detect_opportunity_types(self, text: str) -> List[str]:
        """检测投资机会类型"""
        detected_types = []
        
        for opp_type, keywords in self.opportunity_keywords.items():
            if any(keyword in text for keyword in keywords):
                detected_types.append(opp_type)
        
        return detected_types
    
    def _detect_related_industries(self, text: str) -> List[str]:
        """检测相关行业"""
        detected_industries = []
        
        for industry, keywords in self.industry_keywords.items():
            if any(keyword in text for keyword in keywords):
                detected_industries.append(industry)
        
        return detected_industries
    
    def _calculate_opportunity_score(self, sentiment: Dict, opp_types: List, industries: List) -> float:
        """计算投资机会评分"""
        base_score = sentiment.get("final_sentiment_score", 0)
        confidence = sentiment.get("confidence", 0.5)
        
        # 基于情感评分
        if base_score > 5:
            score = 8.0
        elif base_score > 2:
            score = 6.0
        elif base_score > 0:
            score = 4.0
        else:
            score = 2.0
        
        # 机会类型加分
        score += len(opp_types) * 0.5
        
        # 行业相关性加分
        score += len(industries) * 0.3
        
        # 置信度调整
        score *= confidence
        
        return min(10.0, max(0.0, score))
    
    def _extract_key_investment_info(self, text: str) -> Dict[str, Any]:
        """提取关键投资信息"""
        info = {
            "mentioned_companies": self._extract_companies(text),
            "financial_numbers": self._extract_financial_numbers(text),
            "time_indicators": self._extract_time_indicators(text),
            "key_events": self._extract_key_events(text)
        }
        return info
    
    def _extract_companies(self, text: str) -> List[str]:
        """提取提及的公司名称"""
        # 简单的公司名称提取（可以用NER改进）
        company_patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*(?:公司|集团|股份|有限)',
            r'([^，。,.\s]{2,8})\s*(?:公司|集团|股份)',
        ]
        
        companies = []
        for pattern in company_patterns:
            matches = re.findall(pattern, text)
            companies.extend(matches)
        
        return list(set(companies))[:5]  # 去重并限制数量
    
    def _extract_financial_numbers(self, text: str) -> List[str]:
        """提取财务数字"""
        number_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:亿|万|千万)\s*(?:元|美元|港元)',
            r'(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*(?:倍|次)'
        ]
        
        numbers = []
        for pattern in number_patterns:
            matches = re.findall(pattern, text)
            numbers.extend(matches)
        
        return numbers[:10]  # 限制数量
    
    def _extract_time_indicators(self, text: str) -> List[str]:
        """提取时间指示符"""
        time_patterns = [
            r'(\d{4}年)',
            r'(\d+月)',
            r'(第[一二三四]\s*季度)',
            r'(上半年|下半年)',
            r'(今年|明年|去年)'
        ]
        
        time_indicators = []
        for pattern in time_patterns:
            matches = re.findall(pattern, text)
            time_indicators.extend(matches)
        
        return list(set(time_indicators))
    
    def _extract_key_events(self, text: str) -> List[str]:
        """提取关键事件"""
        event_keywords = ["发布", "宣布", "签署", "完成", "启动", "推出", "获得", "通过"]
        
        sentences = re.split(r'[。！？.!?]', text)
        key_events = []
        
        for sentence in sentences:
            if any(keyword in sentence for keyword in event_keywords):
                if len(sentence.strip()) > 10:  # 过滤太短的句子
                    key_events.append(sentence.strip())
        
        return key_events[:3]  # 限制数量
    
    def _assess_time_sensitivity(self, text: str) -> str:
        """评估时间敏感性"""
        immediate_words = ["今日", "今天", "刚刚", "立即", "现在"]
        short_term_words = ["本周", "近期", "短期", "即将"]
        
        if any(word in text for word in immediate_words):
            return "immediate"
        elif any(word in text for word in short_term_words):
            return "short_term"
        else:
            return "long_term"
    
    def _calculate_confidence(self, opp_types: List, sentiment: Dict) -> float:
        """计算识别置信度"""
        base_confidence = sentiment.get("confidence", 0.5)
        
        # 基于机会类型数量
        type_bonus = min(0.3, len(opp_types) * 0.1)
        
        # 基于情感强度
        sentiment_score = abs(sentiment.get("final_sentiment_score", 0))
        sentiment_bonus = min(0.2, sentiment_score / 10 * 0.2)
        
        total_confidence = base_confidence + type_bonus + sentiment_bonus
        return min(1.0, total_confidence)
    
    def _filter_high_value_opportunities(self, opportunities: List[Dict]) -> List[Dict]:
        """筛选高价值投资机会"""
        # 筛选条件
        filtered = [
            opp for opp in opportunities
            if opp["opportunity_score"] >= 6.0 and opp["confidence"] >= 0.6
        ]
        
        # 按评分排序
        filtered.sort(key=lambda x: x["opportunity_score"], reverse=True)
        
        return filtered[:10]  # 返回前10个

class RiskAssessmentNode(AsyncNode):
    """
    风险评估节点
    多维度分析投资风险因素
    """
    
    def __init__(self):
        super().__init__()
        # 风险关键词
        self.risk_keywords = {
            "market_risk": ["波动", "不确定", "风险", "下跌", "调整", "震荡"],
            "policy_risk": ["监管", "政策", "法规", "合规", "审查", "限制"],
            "financial_risk": ["债务", "负债", "亏损", "资金", "流动性", "偿债"],
            "operational_risk": ["停产", "停业", "故障", "事故", "质量", "安全"],
            "competition_risk": ["竞争", "同质化", "价格战", "市场份额", "替代"],
            "external_risk": ["疫情", "灾害", "国际", "贸易", "汇率", "原材料"]
        }
    
    async def run_async(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        风险评估逻辑
        
        Args:
            data: 包含investment opportunities的数据
            
        Returns:
            风险评估结果
        """
        articles = data.get("processed_articles", [])
        opportunities = data.get("investment_opportunities", [])
        sentiment_results = data.get("integrated_sentiment_results", [])
        
        risk_assessments = []
        
        for article, opportunity, sentiment in zip(articles, opportunities, sentiment_results):
            risk_assessment = self._assess_investment_risk(article, opportunity, sentiment)
            risk_assessments.append(risk_assessment)
        
        logger.info(f"风险评估完成: {len(risk_assessments)} 项评估")
        
        return {
            **data,
            "risk_assessments": risk_assessments,
            "overall_risk_level": self._calculate_overall_risk(risk_assessments)
        }
    
    def _assess_investment_risk(self, article: Dict, opportunity: Dict, sentiment: Dict) -> Dict[str, Any]:
        """评估单项投资风险"""
        title = article.get("clean_title", "")
        content = article.get("clean_content", "")
        text = f"{title} {content}"
        
        # 检测风险因子
        risk_factors = self._detect_risk_factors(text)
        
        # 计算风险评分
        risk_score = self._calculate_risk_score(risk_factors, sentiment, opportunity)
        
        # 风险等级
        risk_level = self._determine_risk_level(risk_score)
        
        return {
            "article_index": article.get("article_index", 0),
            "risk_factors": risk_factors,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_details": self._generate_risk_details(risk_factors, text),
            "mitigation_suggestions": self._suggest_mitigation(risk_factors)
        }
    
    def _detect_risk_factors(self, text: str) -> Dict[str, List[str]]:
        """检测风险因子"""
        detected_risks = {}
        
        for risk_type, keywords in self.risk_keywords.items():
            matches = [kw for kw in keywords if kw in text]
            if matches:
                detected_risks[risk_type] = matches
        
        return detected_risks
    
    def _calculate_risk_score(self, risk_factors: Dict, sentiment: Dict, opportunity: Dict) -> float:
        """计算风险评分"""
        base_risk = 5.0  # 基础风险
        
        # 基于检测到的风险因子
        risk_factor_score = len(risk_factors) * 1.5
        
        # 基于情感评分（负面情感增加风险）
        sentiment_score = sentiment.get("final_sentiment_score", 0)
        if sentiment_score < 0:
            sentiment_risk = abs(sentiment_score) * 0.5
        else:
            sentiment_risk = -sentiment_score * 0.2  # 正面情感降低风险
        
        # 基于机会评分（高机会通常伴随高风险）
        opportunity_score = opportunity.get("opportunity_score", 5)
        opportunity_risk = (opportunity_score - 5) * 0.3
        
        total_risk = base_risk + risk_factor_score + sentiment_risk + opportunity_risk
        
        return min(10.0, max(0.0, total_risk))
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """确定风险等级"""
        if risk_score >= 8:
            return "高风险"
        elif risk_score >= 6:
            return "中高风险"
        elif risk_score >= 4:
            return "中等风险"
        elif risk_score >= 2:
            return "低风险"
        else:
            return "极低风险"
    
    def _generate_risk_details(self, risk_factors: Dict, text: str) -> List[str]:
        """生成风险详情"""
        details = []
        
        for risk_type, keywords in risk_factors.items():
            risk_desc = {
                "market_risk": "市场波动风险",
                "policy_risk": "政策监管风险",
                "financial_risk": "财务风险",
                "operational_risk": "经营风险",
                "competition_risk": "竞争风险",
                "external_risk": "外部环境风险"
            }.get(risk_type, risk_type)
            
            detail = f"{risk_desc}: 检测到关键词 {', '.join(keywords[:3])}"
            details.append(detail)
        
        return details
    
    def _suggest_mitigation(self, risk_factors: Dict) -> List[str]:
        """建议风险缓解措施"""
        suggestions = []
        
        mitigation_map = {
            "market_risk": "建议分散投资，控制仓位，设置止损",
            "policy_risk": "关注政策动向，及时调整策略",
            "financial_risk": "审慎分析财务状况，避免高杠杆",
            "operational_risk": "深入了解公司经营状况",
            "competition_risk": "关注行业竞争格局变化",
            "external_risk": "密切关注外部环境变化"
        }
        
        for risk_type in risk_factors.keys():
            if risk_type in mitigation_map:
                suggestions.append(mitigation_map[risk_type])
        
        return suggestions
    
    def _calculate_overall_risk(self, risk_assessments: List[Dict]) -> Dict[str, Any]:
        """计算整体风险水平"""
        if not risk_assessments:
            return {"level": "未知", "score": 5.0}
        
        avg_risk_score = sum(r["risk_score"] for r in risk_assessments) / len(risk_assessments)
        
        # 统计风险等级分布
        risk_distribution = {}
        for assessment in risk_assessments:
            level = assessment["risk_level"]
            risk_distribution[level] = risk_distribution.get(level, 0) + 1
        
        return {
            "level": self._determine_risk_level(avg_risk_score),
            "score": round(avg_risk_score, 2),
            "distribution": risk_distribution,
            "high_risk_count": len([r for r in risk_assessments if r["risk_score"] >= 7])
        }

class StockCorrelationNode(AsyncNode):
    """
    股票关联分析节点
    分析新闻与具体股票的关联度
    """
    
    async def run_async(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        股票关联分析逻辑
        """
        articles = data.get("processed_articles", [])
        opportunities = data.get("investment_opportunities", [])
        
        correlations = []
        
        for article, opportunity in zip(articles, opportunities):
            correlation = self._analyze_stock_correlation(article, opportunity)
            correlations.append(correlation)
        
        logger.info(f"股票关联分析完成: {len(correlations)} 项分析")
        
        return {
            **data,
            "stock_correlations": correlations,
            "recommended_stocks": self._recommend_stocks(correlations)
        }
    
    def _analyze_stock_correlation(self, article: Dict, opportunity: Dict) -> Dict[str, Any]:
        """分析股票关联度"""
        # 简化实现 - 实际应该结合股票数据库
        companies = opportunity.get("key_information", {}).get("mentioned_companies", [])
        industries = opportunity.get("related_industries", [])
        
        return {
            "article_index": article.get("article_index", 0),
            "mentioned_companies": companies,
            "related_industries": industries,
            "correlation_strength": self._calculate_correlation_strength(companies, industries),
            "investment_themes": self._identify_investment_themes(opportunity)
        }
    
    def _calculate_correlation_strength(self, companies: List, industries: List) -> str:
        """计算关联强度"""
        if len(companies) >= 2:
            return "强关联"
        elif len(companies) == 1 or len(industries) >= 2:
            return "中等关联"
        elif len(industries) == 1:
            return "弱关联"
        else:
            return "无直接关联"
    
    def _identify_investment_themes(self, opportunity: Dict) -> List[str]:
        """识别投资主题"""
        themes = []
        
        opp_types = opportunity.get("opportunity_types", [])
        industries = opportunity.get("related_industries", [])
        
        # 基于机会类型生成主题
        theme_mapping = {
            "policy_support": "政策利好",
            "technology_breakthrough": "技术创新",
            "market_expansion": "市场扩张",
            "financial_improvement": "业绩改善"
        }
        
        for opp_type in opp_types:
            if opp_type in theme_mapping:
                themes.append(theme_mapping[opp_type])
        
        # 基于行业生成主题
        for industry in industries:
            themes.append(f"{industry}板块")
        
        return list(set(themes))
    
    def _recommend_stocks(self, correlations: List[Dict]) -> List[Dict]:
        """推荐相关股票"""
        recommendations = []
        
        for correlation in correlations:
            if correlation["correlation_strength"] in ["强关联", "中等关联"]:
                rec = {
                    "article_index": correlation["article_index"],
                    "companies": correlation["mentioned_companies"],
                    "themes": correlation["investment_themes"],
                    "strength": correlation["correlation_strength"]
                }
                recommendations.append(rec)
        
        return recommendations

class InvestmentAdviceGenerationNode(AsyncNode):
    """
    投资建议生成节点
    综合所有分析结果，生成最终的投资建议
    """
    
    async def run_async(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        投资建议生成逻辑
        """
        opportunities = data.get("investment_opportunities", [])
        risk_assessments = data.get("risk_assessments", [])
        stock_correlations = data.get("stock_correlations", [])
        sentiment_results = data.get("integrated_sentiment_results", [])
        
        investment_advice = []
        
        for i, (opp, risk, correlation, sentiment) in enumerate(
            zip(opportunities, risk_assessments, stock_correlations, sentiment_results)
        ):
            advice = self._generate_investment_advice(opp, risk, correlation, sentiment)
            investment_advice.append(advice)
        
        # 生成综合投资策略
        overall_strategy = self._generate_overall_strategy(investment_advice)
        
        logger.info(f"投资建议生成完成: {len(investment_advice)} 项建议")
        
        return {
            "investment_advice": investment_advice,
            "overall_investment_strategy": overall_strategy,
            "actionable_recommendations": self._filter_actionable_advice(investment_advice),
            "generation_timestamp": datetime.now().isoformat()
        }
    
    def _generate_investment_advice(
        self, 
        opportunity: Dict, 
        risk: Dict, 
        correlation: Dict, 
        sentiment: Dict
    ) -> Dict[str, Any]:
        """生成单项投资建议"""
        
        # 投资动作决策
        action = self._determine_investment_action(opportunity, risk, sentiment)
        
        # 仓位建议
        position_size = self._recommend_position_size(opportunity, risk)
        
        # 时间框架
        time_horizon = self._determine_time_horizon(opportunity)
        
        # 建议理由
        rationale = self._generate_rationale(opportunity, risk, sentiment)
        
        return {
            "article_index": opportunity.get("article_index", 0),
            "investment_action": action,
            "position_size": position_size,
            "time_horizon": time_horizon,
            "rationale": rationale,
            "confidence": self._calculate_advice_confidence(opportunity, risk, sentiment),
            "key_points": self._extract_key_points(opportunity, correlation),
            "risk_warnings": risk.get("risk_details", []),
            "target_companies": correlation.get("mentioned_companies", []),
            "investment_themes": correlation.get("investment_themes", [])
        }
    
    def _determine_investment_action(self, opportunity: Dict, risk: Dict, sentiment: Dict) -> str:
        """确定投资动作"""
        opp_score = opportunity.get("opportunity_score", 5)
        risk_score = risk.get("risk_score", 5)
        sentiment_score = sentiment.get("final_sentiment_score", 0)
        
        # 综合评分
        combined_score = opp_score - (risk_score - 5) + sentiment_score * 0.5
        
        if combined_score >= 8:
            return "强烈买入"
        elif combined_score >= 6:
            return "买入"
        elif combined_score >= 4:
            return "关注"
        elif combined_score >= 2:
            return "谨慎观望"
        else:
            return "规避"
    
    def _recommend_position_size(self, opportunity: Dict, risk: Dict) -> str:
        """推荐仓位大小"""
        opp_score = opportunity.get("opportunity_score", 5)
        risk_score = risk.get("risk_score", 5)
        
        # 高机会低风险 = 大仓位
        # 低机会高风险 = 小仓位
        score_diff = opp_score - risk_score
        
        if score_diff >= 3:
            return "重仓 (30-50%)"
        elif score_diff >= 1:
            return "中等仓位 (15-30%)"
        elif score_diff >= -1:
            return "轻仓 (5-15%)"
        else:
            return "观望 (0%)"
    
    def _determine_time_horizon(self, opportunity: Dict) -> str:
        """确定投资时间框架"""
        time_sensitivity = opportunity.get("time_sensitivity", "long_term")
        
        mapping = {
            "immediate": "超短线 (1-7天)",
            "short_term": "短线 (1-4周)",
            "long_term": "中长线 (3-12个月)"
        }
        
        return mapping.get(time_sensitivity, "中长线 (3-12个月)")
    
    def _generate_rationale(self, opportunity: Dict, risk: Dict, sentiment: Dict) -> str:
        """生成投资理由"""
        reasons = []
        
        # 基于机会类型
        opp_types = opportunity.get("opportunity_types", [])
        if "policy_support" in opp_types:
            reasons.append("政策支持利好")
        if "technology_breakthrough" in opp_types:
            reasons.append("技术突破驱动")
        if "financial_improvement" in opp_types:
            reasons.append("基本面改善")
        
        # 基于情感分析
        sentiment_score = sentiment.get("final_sentiment_score", 0)
        if sentiment_score > 3:
            reasons.append("市场情绪积极")
        elif sentiment_score < -3:
            reasons.append("市场情绪消极")
        
        # 基于风险水平
        risk_level = risk.get("risk_level", "")
        if "低风险" in risk_level:
            reasons.append("风险相对可控")
        elif "高风险" in risk_level:
            reasons.append("需警惕高风险")
        
        return "、".join(reasons) if reasons else "综合分析结果"
    
    def _calculate_advice_confidence(self, opportunity: Dict, risk: Dict, sentiment: Dict) -> float:
        """计算建议置信度"""
        opp_confidence = opportunity.get("confidence", 0.5)
        sentiment_confidence = sentiment.get("confidence", 0.5)
        
        # 简单平均
        avg_confidence = (opp_confidence + sentiment_confidence) / 2
        
        # 基于风险调整
        risk_score = risk.get("risk_score", 5)
        if risk_score > 7:
            avg_confidence *= 0.8  # 高风险降低置信度
        
        return round(avg_confidence, 2)
    
    def _extract_key_points(self, opportunity: Dict, correlation: Dict) -> List[str]:
        """提取关键要点"""
        points = []
        
        # 机会要点
        opp_types = opportunity.get("opportunity_types", [])
        for opp_type in opp_types[:2]:  # 限制数量
            points.append(f"投资机会: {opp_type}")
        
        # 相关公司
        companies = correlation.get("mentioned_companies", [])
        if companies:
            points.append(f"相关公司: {', '.join(companies[:3])}")
        
        # 投资主题
        themes = correlation.get("investment_themes", [])
        if themes:
            points.append(f"投资主题: {', '.join(themes[:2])}")
        
        return points
    
    def _generate_overall_strategy(self, advice_list: List[Dict]) -> Dict[str, Any]:
        """生成整体投资策略"""
        if not advice_list:
            return {}
        
        # 统计投资动作分布
        action_counts = {}
        for advice in advice_list:
            action = advice["investment_action"]
            action_counts[action] = action_counts.get(action, 0) + 1
        
        # 找出主导策略
        dominant_action = max(action_counts.items(), key=lambda x: x[1])[0]
        
        # 计算平均置信度
        avg_confidence = sum(a["confidence"] for a in advice_list) / len(advice_list)
        
        # 收集所有投资主题
        all_themes = []
        for advice in advice_list:
            all_themes.extend(advice.get("investment_themes", []))
        
        # 主题频次统计
        theme_counts = {}
        for theme in all_themes:
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        top_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "dominant_strategy": dominant_action,
            "strategy_confidence": round(avg_confidence, 2),
            "action_distribution": action_counts,
            "top_investment_themes": [theme for theme, count in top_themes],
            "total_opportunities": len(advice_list),
            "actionable_count": len([a for a in advice_list if a["investment_action"] in ["买入", "强烈买入"]])
        }
    
    def _filter_actionable_advice(self, advice_list: List[Dict]) -> List[Dict]:
        """筛选可执行的投资建议"""
        actionable = [
            advice for advice in advice_list
            if advice["investment_action"] in ["买入", "强烈买入", "关注"]
            and advice["confidence"] >= 0.6
        ]
        
        # 按置信度排序
        actionable.sort(key=lambda x: x["confidence"], reverse=True)
        
        return actionable[:10]  # 返回前10个

class InvestmentAnalysisFlow:
    """
    投资分析主工作流
    使用PocketFlow实现完整的投资分析流水线
    """
    
    def __init__(self):
        # 创建处理节点
        self.opportunity_identification = InvestmentOpportunityNode()
        self.risk_assessment = RiskAssessmentNode()
        self.stock_correlation = StockCorrelationNode()
        self.advice_generation = InvestmentAdviceGenerationNode()
    
    async def analyze_investment(self, articles_with_sentiment: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行投资分析
        
        Args:
            articles_with_sentiment: 包含情感分析结果的文章数据
            
        Returns:
            完整的投资分析结果
        """
        logger.info("开始投资分析工作流")
        
        # 创建PocketFlow流水线
        flow = AsyncFlow(start=self.opportunity_identification)
        flow = flow.next(self.risk_assessment)
        flow = flow.next(self.stock_correlation)
        flow = flow.next(self.advice_generation)
        
        # 执行工作流
        result = await flow.run_async(articles_with_sentiment)
        
        logger.info("投资分析工作流完成")
        return result

# 便捷接口
async def analyze_investment_opportunities(
    articles_with_sentiment: Dict[str, Any]
) -> Dict[str, Any]:
    """
    便捷的投资分析接口
    
    Args:
        articles_with_sentiment: 包含情感分析结果的文章数据
        
    Returns:
        投资分析结果
    """
    flow = InvestmentAnalysisFlow()
    return await flow.analyze_investment(articles_with_sentiment) 