#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
投资分析器

专业的投资分析工具，支持：
- 投资机会识别和评估
- 多维度风险分析
- 投资建议生成
- 组合风险管理
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class InvestmentOpportunity:
    """投资机会数据结构"""
    opportunity_type: str  # 机会类型
    industry: str         # 相关行业
    score: float          # 机会评分 0-10
    confidence: float     # 置信度 0-1
    time_horizon: str     # 时间框架
    key_factors: List[str]  # 关键因素
    related_companies: List[str]  # 相关公司

@dataclass
class RiskAssessment:
    """风险评估数据结构"""
    risk_level: str       # 风险等级
    risk_score: float     # 风险评分 0-10
    risk_factors: List[str]  # 风险因素
    mitigation_strategies: List[str]  # 缓解策略
    risk_breakdown: Dict[str, float]  # 风险分解

@dataclass
class InvestmentAdvice:
    """投资建议数据结构"""
    action: str           # 投资动作
    position_size: str    # 仓位建议
    time_frame: str       # 时间框架
    rationale: str        # 投资理由
    confidence: float     # 建议置信度
    target_price: Optional[float]  # 目标价格
    stop_loss: Optional[float]     # 止损位

class InvestmentOpportunityDetector:
    """投资机会检测器"""
    
    def __init__(self):
        # 投资机会关键词库
        self.opportunity_keywords = {
            "policy_driven": {
                "keywords": ["政策", "支持", "扶持", "减税", "补贴", "优惠", "鼓励", "规划", "政府"],
                "weight": 2.5,
                "industries": ["新能源", "科技", "医疗", "基建"]
            },
            "technology_breakthrough": {
                "keywords": ["突破", "创新", "技术", "研发", "专利", "升级", "革命", "颠覆"],
                "weight": 2.8,
                "industries": ["科技", "医疗", "制造"]
            },
            "market_expansion": {
                "keywords": ["扩张", "增长", "需求", "订单", "合同", "业务", "拓展", "布局"],
                "weight": 2.0,
                "industries": ["消费", "科技", "服务"]
            },
            "financial_improvement": {
                "keywords": ["盈利", "收入", "营收", "业绩", "增长", "回升", "改善", "好转"],
                "weight": 2.3,
                "industries": ["全行业"]
            },
            "strategic_cooperation": {
                "keywords": ["合作", "联盟", "并购", "重组", "投资", "合资", "战略", "协议"],
                "weight": 2.2,
                "industries": ["全行业"]
            },
            "industry_transformation": {
                "keywords": ["转型", "升级", "数字化", "智能化", "绿色", "低碳", "新模式"],
                "weight": 2.6,
                "industries": ["制造", "能源", "金融"]
            }
        }
        
        # 行业关键词映射
        self.industry_mapping = {
            "科技": ["科技", "互联网", "人工智能", "AI", "芯片", "半导体", "软件", "云计算", "大数据"],
            "医疗": ["医疗", "医药", "生物", "疫苗", "药品", "医院", "健康", "医学", "诊断"],
            "金融": ["银行", "保险", "证券", "金融", "支付", "理财", "信贷", "投资", "基金"],
            "能源": ["能源", "电力", "新能源", "光伏", "风电", "电池", "储能", "煤炭", "石油"],
            "消费": ["消费", "零售", "电商", "品牌", "食品", "饮料", "服装", "家电", "汽车"],
            "制造": ["制造", "工业", "机械", "化工", "材料", "钢铁", "有色", "建材"],
            "基建": ["基建", "建筑", "建设", "交通", "水利", "环保", "市政"]
        }
    
    def detect_opportunities(self, text: str, sentiment_score: float = 0) -> List[InvestmentOpportunity]:
        """
        检测投资机会
        
        Args:
            text: 分析文本
            sentiment_score: 情感评分
            
        Returns:
            投资机会列表
        """
        opportunities = []
        
        # 检测各类投资机会
        for opp_type, config in self.opportunity_keywords.items():
            opportunity = self._detect_specific_opportunity(text, opp_type, config, sentiment_score)
            if opportunity and opportunity.score >= 4.0:  # 筛选高质量机会
                opportunities.append(opportunity)
        
        # 按评分排序
        opportunities.sort(key=lambda x: x.score, reverse=True)
        
        return opportunities
    
    def _detect_specific_opportunity(
        self, 
        text: str, 
        opp_type: str, 
        config: Dict, 
        sentiment_score: float
    ) -> Optional[InvestmentOpportunity]:
        """检测特定类型的投资机会"""
        
        # 关键词匹配
        keywords = config["keywords"]
        matched_keywords = [kw for kw in keywords if kw in text]
        
        if not matched_keywords:
            return None
        
        # 计算基础分数
        keyword_score = len(matched_keywords) * config["weight"]
        
        # 情感加成
        sentiment_bonus = max(0, sentiment_score) * 0.3
        
        # 识别相关行业
        related_industry = self._identify_industry(text)
        
        # 行业相关性调整
        industry_bonus = 0
        if related_industry in config.get("industries", []) or "全行业" in config.get("industries", []):
            industry_bonus = 1.0
        
        # 时间敏感性分析
        time_horizon = self._analyze_time_sensitivity(text)
        
        # 时间框架调整
        time_bonus = {"immediate": 1.2, "short_term": 1.0, "long_term": 0.8}.get(time_horizon, 1.0)
        
        # 提取关键因素
        key_factors = self._extract_key_factors(text, matched_keywords)
        
        # 提取相关公司
        related_companies = self._extract_companies(text)
        
        # 计算最终评分
        final_score = (keyword_score + sentiment_bonus + industry_bonus) * time_bonus
        final_score = min(10.0, max(0.0, final_score))
        
        # 计算置信度
        confidence = self._calculate_opportunity_confidence(
            matched_keywords, related_industry, key_factors, len(text)
        )
        
        return InvestmentOpportunity(
            opportunity_type=opp_type,
            industry=related_industry,
            score=round(final_score, 2),
            confidence=round(confidence, 2),
            time_horizon=time_horizon,
            key_factors=key_factors,
            related_companies=related_companies
        )
    
    def _identify_industry(self, text: str) -> str:
        """识别相关行业"""
        industry_scores = {}
        
        for industry, keywords in self.industry_mapping.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                industry_scores[industry] = score
        
        if industry_scores:
            return max(industry_scores.items(), key=lambda x: x[1])[0]
        else:
            return "未明确"
    
    def _analyze_time_sensitivity(self, text: str) -> str:
        """分析时间敏感性"""
        immediate_words = ["今日", "今天", "刚刚", "立即", "马上", "现在", "紧急"]
        short_term_words = ["本周", "近期", "短期", "即将", "很快", "本月"]
        long_term_words = ["长期", "未来", "计划", "预期", "目标", "战略"]
        
        if any(word in text for word in immediate_words):
            return "immediate"
        elif any(word in text for word in short_term_words):
            return "short_term"
        elif any(word in text for word in long_term_words):
            return "long_term"
        else:
            return "medium_term"
    
    def _extract_key_factors(self, text: str, matched_keywords: List[str]) -> List[str]:
        """提取关键因素"""
        factors = []
        
        # 基于匹配的关键词提取相关句子
        sentences = re.split(r'[。！？.!?]', text)
        
        for sentence in sentences:
            if any(keyword in sentence for keyword in matched_keywords):
                if len(sentence.strip()) > 10:  # 过滤太短的句子
                    factors.append(sentence.strip())
        
        return factors[:3]  # 限制数量
    
    def _extract_companies(self, text: str) -> List[str]:
        """提取相关公司"""
        # 简单的公司名称提取模式
        company_patterns = [
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*(?:公司|集团|股份|有限)',
            r'([^\s，。,.\d]{2,6})\s*(?:公司|集团|股份)',
        ]
        
        companies = []
        for pattern in company_patterns:
            matches = re.findall(pattern, text)
            companies.extend(matches)
        
        # 去重并限制数量
        return list(set(companies))[:5]
    
    def _calculate_opportunity_confidence(
        self, 
        matched_keywords: List[str], 
        industry: str, 
        key_factors: List[str], 
        text_length: int
    ) -> float:
        """计算机会识别置信度"""
        base_confidence = 0.5
        
        # 关键词数量加成
        keyword_bonus = min(0.3, len(matched_keywords) * 0.1)
        
        # 行业明确性加成
        industry_bonus = 0.1 if industry != "未明确" else 0
        
        # 关键因素加成
        factor_bonus = min(0.2, len(key_factors) * 0.07)
        
        # 文本长度调整
        length_bonus = min(0.1, text_length / 1000)
        
        total_confidence = base_confidence + keyword_bonus + industry_bonus + factor_bonus + length_bonus
        
        return min(1.0, total_confidence)

class RiskAnalyzer:
    """风险分析器"""
    
    def __init__(self):
        # 风险因子库
        self.risk_factors = {
            "market_risk": {
                "keywords": ["波动", "不确定", "风险", "下跌", "调整", "震荡", "不稳定"],
                "weight": 1.5,
                "description": "市场波动风险"
            },
            "policy_risk": {
                "keywords": ["监管", "政策", "法规", "合规", "审查", "限制", "禁止"],
                "weight": 2.0,
                "description": "政策监管风险"
            },
            "financial_risk": {
                "keywords": ["债务", "负债", "亏损", "资金", "流动性", "偿债", "财务"],
                "weight": 2.2,
                "description": "财务风险"
            },
            "operational_risk": {
                "keywords": ["停产", "停业", "故障", "事故", "质量", "安全", "运营"],
                "weight": 1.8,
                "description": "经营风险"
            },
            "competition_risk": {
                "keywords": ["竞争", "同质化", "价格战", "市场份额", "替代", "挤压"],
                "weight": 1.6,
                "description": "竞争风险"
            },
            "external_risk": {
                "keywords": ["疫情", "灾害", "国际", "贸易", "汇率", "原材料", "供应链"],
                "weight": 1.7,
                "description": "外部环境风险"
            }
        }
    
    def analyze_risk(
        self, 
        text: str, 
        opportunity: InvestmentOpportunity, 
        sentiment_score: float = 0
    ) -> RiskAssessment:
        """
        分析投资风险
        
        Args:
            text: 分析文本
            opportunity: 投资机会
            sentiment_score: 情感评分
            
        Returns:
            风险评估结果
        """
        # 检测各类风险因子
        detected_risks = self._detect_risk_factors(text)
        
        # 计算风险评分
        risk_score = self._calculate_risk_score(detected_risks, opportunity, sentiment_score)
        
        # 确定风险等级
        risk_level = self._determine_risk_level(risk_score)
        
        # 生成缓解策略
        mitigation_strategies = self._generate_mitigation_strategies(detected_risks, opportunity)
        
        # 风险分解
        risk_breakdown = self._calculate_risk_breakdown(detected_risks)
        
        return RiskAssessment(
            risk_level=risk_level,
            risk_score=round(risk_score, 2),
            risk_factors=[self.risk_factors[rf]["description"] for rf in detected_risks.keys()],
            mitigation_strategies=mitigation_strategies,
            risk_breakdown=risk_breakdown
        )
    
    def _detect_risk_factors(self, text: str) -> Dict[str, List[str]]:
        """检测风险因子"""
        detected_risks = {}
        
        for risk_type, config in self.risk_factors.items():
            matched_keywords = [kw for kw in config["keywords"] if kw in text]
            if matched_keywords:
                detected_risks[risk_type] = matched_keywords
        
        return detected_risks
    
    def _calculate_risk_score(
        self, 
        detected_risks: Dict[str, List[str]], 
        opportunity: InvestmentOpportunity, 
        sentiment_score: float
    ) -> float:
        """计算风险评分"""
        base_risk = 3.0  # 基础风险
        
        # 基于检测到的风险因子
        risk_factor_score = 0
        for risk_type, keywords in detected_risks.items():
            weight = self.risk_factors[risk_type]["weight"]
            risk_factor_score += len(keywords) * weight
        
        # 情感评分调整（负面情感增加风险）
        sentiment_adjustment = 0
        if sentiment_score < 0:
            sentiment_adjustment = abs(sentiment_score) * 0.4
        elif sentiment_score > 0:
            sentiment_adjustment = -sentiment_score * 0.2  # 正面情感降低风险
        
        # 机会评分调整（高机会可能伴随高风险）
        opportunity_adjustment = 0
        if opportunity.score > 7:
            opportunity_adjustment = (opportunity.score - 7) * 0.3
        
        # 时间框架调整
        time_adjustment = {"immediate": 0.5, "short_term": 0.2, "medium_term": 0, "long_term": -0.3}.get(
            opportunity.time_horizon, 0
        )
        
        total_risk = base_risk + risk_factor_score + sentiment_adjustment + opportunity_adjustment + time_adjustment
        
        return min(10.0, max(0.0, total_risk))
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """确定风险等级"""
        if risk_score >= 8:
            return "极高风险"
        elif risk_score >= 6:
            return "高风险"
        elif risk_score >= 4:
            return "中等风险"
        elif risk_score >= 2:
            return "低风险"
        else:
            return "极低风险"
    
    def _generate_mitigation_strategies(
        self, 
        detected_risks: Dict[str, List[str]], 
        opportunity: InvestmentOpportunity
    ) -> List[str]:
        """生成风险缓解策略"""
        strategies = []
        
        strategy_mapping = {
            "market_risk": "建议分散投资，控制仓位大小，设置止损点",
            "policy_risk": "密切关注政策动向，及时调整投资策略",
            "financial_risk": "深入分析财务状况，避免高杠杆投资",
            "operational_risk": "关注公司经营状况和管理质量",
            "competition_risk": "评估行业竞争格局和公司护城河",
            "external_risk": "关注宏观经济环境和国际形势变化"
        }
        
        for risk_type in detected_risks.keys():
            if risk_type in strategy_mapping:
                strategies.append(strategy_mapping[risk_type])
        
        # 基于机会特征的策略
        if opportunity.time_horizon == "immediate":
            strategies.append("短期操作需要快进快出，严格止损")
        elif opportunity.time_horizon == "long_term":
            strategies.append("长期投资需要耐心持有，定期评估")
        
        return strategies
    
    def _calculate_risk_breakdown(self, detected_risks: Dict[str, List[str]]) -> Dict[str, float]:
        """计算风险分解"""
        breakdown = {}
        total_weight = 0
        
        for risk_type, keywords in detected_risks.items():
            weight = self.risk_factors[risk_type]["weight"] * len(keywords)
            breakdown[self.risk_factors[risk_type]["description"]] = weight
            total_weight += weight
        
        # 标准化
        if total_weight > 0:
            for risk_desc in breakdown:
                breakdown[risk_desc] = round(breakdown[risk_desc] / total_weight * 100, 1)
        
        return breakdown

class InvestmentAdviceGenerator:
    """投资建议生成器"""
    
    def __init__(self):
        # 投资动作映射
        self.action_mapping = {
            (8, 10, 0, 4): "强烈买入",
            (6, 8, 0, 6): "买入", 
            (4, 6, 0, 8): "谨慎买入",
            (2, 4, 0, 10): "观望",
            (0, 2, 0, 10): "规避"
        }
    
    def generate_advice(
        self, 
        opportunity: InvestmentOpportunity, 
        risk_assessment: RiskAssessment,
        market_context: Dict[str, Any] = None
    ) -> InvestmentAdvice:
        """
        生成投资建议
        
        Args:
            opportunity: 投资机会
            risk_assessment: 风险评估
            market_context: 市场环境上下文
            
        Returns:
            投资建议
        """
        # 确定投资动作
        action = self._determine_investment_action(opportunity, risk_assessment)
        
        # 建议仓位大小
        position_size = self._recommend_position_size(opportunity, risk_assessment)
        
        # 确定时间框架
        time_frame = self._determine_time_frame(opportunity, risk_assessment)
        
        # 生成投资理由
        rationale = self._generate_rationale(opportunity, risk_assessment, action)
        
        # 计算建议置信度
        confidence = self._calculate_advice_confidence(opportunity, risk_assessment)
        
        # 设置目标价格和止损位（简化实现）
        target_price, stop_loss = self._calculate_price_targets(opportunity, risk_assessment)
        
        return InvestmentAdvice(
            action=action,
            position_size=position_size,
            time_frame=time_frame,
            rationale=rationale,
            confidence=round(confidence, 2),
            target_price=target_price,
            stop_loss=stop_loss
        )
    
    def _determine_investment_action(
        self, 
        opportunity: InvestmentOpportunity, 
        risk_assessment: RiskAssessment
    ) -> str:
        """确定投资动作"""
        opp_score = opportunity.score
        risk_score = risk_assessment.risk_score
        
        # 综合评分 = 机会评分 - 风险评分 + 置信度调整
        confidence_avg = (opportunity.confidence + (10 - risk_score) / 10) / 2
        combined_score = (opp_score - risk_score + 5) * confidence_avg
        
        if combined_score >= 8:
            return "强烈买入"
        elif combined_score >= 6:
            return "买入"
        elif combined_score >= 4:
            return "谨慎买入"
        elif combined_score >= 2:
            return "观望"
        else:
            return "规避"
    
    def _recommend_position_size(
        self, 
        opportunity: InvestmentOpportunity, 
        risk_assessment: RiskAssessment
    ) -> str:
        """推荐仓位大小"""
        # 基于风险收益比
        risk_reward_ratio = opportunity.score / max(1, risk_assessment.risk_score)
        confidence_factor = (opportunity.confidence + (10 - risk_assessment.risk_score) / 10) / 2
        
        adjusted_ratio = risk_reward_ratio * confidence_factor
        
        if adjusted_ratio >= 2.0:
            return "重仓 (30-50%)"
        elif adjusted_ratio >= 1.5:
            return "中等仓位 (15-30%)"
        elif adjusted_ratio >= 1.0:
            return "轻仓 (5-15%)"
        else:
            return "观望 (0%)"
    
    def _determine_time_frame(
        self, 
        opportunity: InvestmentOpportunity, 
        risk_assessment: RiskAssessment
    ) -> str:
        """确定时间框架"""
        time_mapping = {
            "immediate": "超短线 (1-7天)",
            "short_term": "短线 (1-4周)", 
            "medium_term": "中线 (1-3个月)",
            "long_term": "长线 (3-12个月)"
        }
        
        base_frame = time_mapping.get(opportunity.time_horizon, "中线 (1-3个月)")
        
        # 高风险缩短持有时间
        if risk_assessment.risk_score >= 7:
            if "长线" in base_frame:
                return "中线 (1-3个月)"
            elif "中线" in base_frame:
                return "短线 (1-4周)"
        
        return base_frame
    
    def _generate_rationale(
        self, 
        opportunity: InvestmentOpportunity, 
        risk_assessment: RiskAssessment, 
        action: str
    ) -> str:
        """生成投资理由"""
        reasons = []
        
        # 基于机会类型
        opp_type_desc = {
            "policy_driven": "政策利好驱动",
            "technology_breakthrough": "技术突破带来机遇",
            "market_expansion": "市场扩张前景广阔",
            "financial_improvement": "基本面持续改善",
            "strategic_cooperation": "战略合作价值显现",
            "industry_transformation": "行业转型升级"
        }
        
        if opportunity.opportunity_type in opp_type_desc:
            reasons.append(opp_type_desc[opportunity.opportunity_type])
        
        # 基于评分
        if opportunity.score >= 7:
            reasons.append("投资机会评分较高")
        
        # 基于风险
        if risk_assessment.risk_score <= 4:
            reasons.append("风险相对可控")
        elif risk_assessment.risk_score >= 7:
            reasons.append("需要警惕高风险")
        
        # 基于行业
        if opportunity.industry and opportunity.industry != "未明确":
            reasons.append(f"{opportunity.industry}行业具备投资价值")
        
        # 基于动作调整语气
        if action in ["强烈买入", "买入"]:
            connector = "，建议积极关注"
        elif action == "谨慎买入":
            connector = "，可考虑适当配置"
        else:
            connector = "，建议谨慎观望"
        
        return "；".join(reasons) + connector if reasons else f"综合分析{connector}"
    
    def _calculate_advice_confidence(
        self, 
        opportunity: InvestmentOpportunity, 
        risk_assessment: RiskAssessment
    ) -> float:
        """计算建议置信度"""
        # 机会置信度权重
        opp_weight = 0.4
        
        # 风险评估确定性权重（风险评分越低，确定性越高）
        risk_certainty = (10 - risk_assessment.risk_score) / 10
        risk_weight = 0.3
        
        # 信息完整性权重
        info_completeness = 0.5
        if opportunity.related_companies:
            info_completeness += 0.1
        if opportunity.key_factors:
            info_completeness += 0.1
        if opportunity.industry != "未明确":
            info_completeness += 0.1
        
        info_weight = 0.3
        
        # 加权平均
        total_confidence = (
            opportunity.confidence * opp_weight +
            risk_certainty * risk_weight + 
            info_completeness * info_weight
        )
        
        return min(1.0, total_confidence)
    
    def _calculate_price_targets(
        self, 
        opportunity: InvestmentOpportunity, 
        risk_assessment: RiskAssessment
    ) -> Tuple[Optional[float], Optional[float]]:
        """计算价格目标（简化实现）"""
        # 这里需要结合实际股价数据，暂时返回None
        # 实际实现中应该基于技术分析或估值模型
        return None, None

class InvestmentAnalyzer:
    """投资分析器主类"""
    
    def __init__(self):
        self.opportunity_detector = InvestmentOpportunityDetector()
        self.risk_analyzer = RiskAnalyzer()
        self.advice_generator = InvestmentAdviceGenerator()
    
    def analyze_investment(
        self, 
        text: str, 
        sentiment_score: float = 0,
        market_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        综合投资分析
        
        Args:
            text: 分析文本
            sentiment_score: 情感评分
            market_context: 市场环境上下文
            
        Returns:
            完整的投资分析结果
        """
        try:
            # 检测投资机会
            opportunities = self.opportunity_detector.detect_opportunities(text, sentiment_score)
            
            if not opportunities:
                return {
                    "status": "no_opportunities",
                    "message": "未发现明显投资机会",
                    "analysis_timestamp": datetime.now().isoformat()
                }
            
            # 对每个机会进行风险分析和建议生成
            analysis_results = []
            
            for opportunity in opportunities:
                # 风险分析
                risk_assessment = self.risk_analyzer.analyze_risk(text, opportunity, sentiment_score)
                
                # 生成投资建议
                investment_advice = self.advice_generator.generate_advice(
                    opportunity, risk_assessment, market_context
                )
                
                analysis_results.append({
                    "opportunity": opportunity,
                    "risk_assessment": risk_assessment,
                    "investment_advice": investment_advice
                })
            
            # 生成综合分析
            summary = self._generate_analysis_summary(analysis_results, sentiment_score)
            
            return {
                "status": "success",
                "analysis_results": analysis_results,
                "summary": summary,
                "total_opportunities": len(opportunities),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"投资分析失败: {e}")
            return {
                "status": "error",
                "message": f"分析过程中出现错误: {str(e)}",
                "analysis_timestamp": datetime.now().isoformat()
            }
    
    def _generate_analysis_summary(
        self, 
        analysis_results: List[Dict], 
        sentiment_score: float
    ) -> Dict[str, Any]:
        """生成分析摘要"""
        if not analysis_results:
            return {}
        
        # 统计投资建议分布
        action_counts = {}
        for result in analysis_results:
            action = result["investment_advice"].action
            action_counts[action] = action_counts.get(action, 0) + 1
        
        # 找出最佳机会
        best_opportunity = max(
            analysis_results, 
            key=lambda x: x["opportunity"].score * x["opportunity"].confidence
        )
        
        # 计算平均风险评分
        avg_risk_score = sum(r["risk_assessment"].risk_score for r in analysis_results) / len(analysis_results)
        
        # 收集所有相关行业
        industries = [r["opportunity"].industry for r in analysis_results if r["opportunity"].industry != "未明确"]
        industry_counts = {ind: industries.count(ind) for ind in set(industries)}
        
        return {
            "total_opportunities": len(analysis_results),
            "action_distribution": action_counts,
            "dominant_action": max(action_counts.items(), key=lambda x: x[1])[0] if action_counts else "观望",
            "best_opportunity": {
                "type": best_opportunity["opportunity"].opportunity_type,
                "industry": best_opportunity["opportunity"].industry,
                "score": best_opportunity["opportunity"].score,
                "action": best_opportunity["investment_advice"].action
            },
            "average_risk_score": round(avg_risk_score, 2),
            "risk_level": self.risk_analyzer._determine_risk_level(avg_risk_score),
            "related_industries": industry_counts,
            "sentiment_influence": "积极" if sentiment_score > 2 else "消极" if sentiment_score < -2 else "中性",
            "actionable_opportunities": len([
                r for r in analysis_results 
                if r["investment_advice"].action in ["买入", "强烈买入", "谨慎买入"]
            ])
        }

# 便捷函数
def analyze_investment_text(
    text: str, 
    sentiment_score: float = 0,
    market_context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """便捷的投资分析函数"""
    analyzer = InvestmentAnalyzer()
    return analyzer.analyze_investment(text, sentiment_score, market_context) 