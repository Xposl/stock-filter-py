#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
新闻分析流水线

基于PocketFlow框架的多Agent协作新闻分析系统。
通过四个专业Agent协作，实现从新闻内容到投资建议的完整分析流程。
"""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

# PocketFlow框架导入
from pocketflow import Flow, Node

# 项目内部模块导入
from ..llm_clients.qwen_client import QwenLLMClient
from ..llm_clients.silicon_flow_client import SiliconFlowClient
from ...data_providers.stock_data_factory import StockDataFactory
from ...models.news_source import NewsSource

logger = logging.getLogger(__name__)

@dataclass
class NewsAnalysisResult:
    """新闻分析结果"""
    news_id: str
    news_content: str
    classification: Dict[str, Any]
    industry_analysis: Dict[str, Any]
    related_stocks: List[Dict[str, Any]]
    investment_advice: Dict[str, Any]
    analysis_time: datetime
    confidence_score: float
    processing_time: float

class NewsClassifierAgent(Node):
    """新闻分类器Agent - 快速判断新闻性质和重要性"""
    
    def __init__(self, llm_client: QwenLLMClient):
        super().__init__()
        self.llm_client = llm_client
    
    def prep(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """准备分类所需的数据"""
        return {
            "news_content": shared_store.get("news_content", ""),
            "shared_store": shared_store  # 传递共享存储的引用
        }
    
    def exec(self, prep_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行新闻分类 - 同步方法"""
        return asyncio.run(self._exec_async(prep_data))
    
    async def _exec_async(self, prep_data: Dict[str, Any]) -> Dict[str, Any]:
        """异步执行新闻分类"""
        news_content = prep_data.get("news_content", "")
        
        if not news_content:
            logger.error("新闻内容为空")
            return {"error": "新闻内容为空", "action": "error"}
        
        prompt = self._build_classification_prompt(news_content)
        
        try:
            async with self.llm_client as client:
                response = await client.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=500
                )
            
            # 解析分类结果
            classification = self._parse_classification_response(response.content)
            
            # 判断是否值得进一步分析
            if classification.get("worth_analysis", False):
                logger.info(f"新闻分类完成，重要性评分: {classification.get('importance_score', 0)}")
                action = "analyze_industry"
            else:
                logger.info("新闻被判定为不值得投资分析，跳过后续步骤")
                action = "skip"
            
            return {
                "classification": classification,
                "action": action
            }
        
        except Exception as e:
            logger.error(f"新闻分类失败: {e}")
            return {
                "error": str(e),
                "action": "error"
            }
    
    def post(self, shared_store: Dict[str, Any], prep_data: Dict[str, Any], exec_result: Dict[str, Any]) -> str:
        """后处理 - 保存结果到共享存储并返回下一步动作"""
        if "classification" in exec_result:
            shared_store["classification"] = exec_result["classification"]
        
        if "error" in exec_result:
            shared_store["error"] = exec_result["error"]
        
        return exec_result.get("action", "error")
    
    def _build_classification_prompt(self, news_content: str) -> str:
        """构建新闻分类Prompt"""
        return f"""你是一个专业的金融新闻分类器。请分析以下新闻并提供结构化输出：

新闻内容：
{news_content[:2000]}  # 限制长度避免token超限

请从以下维度分析：
1. 新闻类型：[政策/财报/市场/技术/人事/并购/IPO/其他]
2. 重要性评分：1-10分（10分最重要，考虑对股市的潜在影响）
3. 涉及实体：提取公司名、行业名、产品名（最多5个）
4. 情感倾向：[正面/负面/中性]
5. 是否值得投资分析：[true/false]

返回JSON格式：
{{
  "news_type": "类型",
  "importance_score": 分数,
  "entities": ["实体1", "实体2"],
  "sentiment": "倾向",
  "worth_analysis": true/false,
  "reason": "判断理由"
}}"""
    
    def _parse_classification_response(self, response_text: str) -> Dict[str, Any]:
        """解析分类响应"""
        try:
            # 尝试提取JSON部分
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                raise ValueError("无法找到有效的JSON内容")
        
        except Exception as e:
            logger.error(f"解析分类结果失败: {e}")
            # 返回默认结果
            return {
                "news_type": "其他",
                "importance_score": 5,
                "entities": [],
                "sentiment": "中性",
                "worth_analysis": True,
                "reason": "解析失败，使用默认值"
            }

class IndustryAnalyzerAgent(Node):
    """行业分析器Agent - 确定新闻利好/利空的行业领域"""
    
    def __init__(self, llm_client: QwenLLMClient):
        super().__init__()
        self.llm_client = llm_client
    
    def prep(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """准备行业分析所需的数据"""
        return {
            "news_content": shared_store.get("news_content", ""),
            "classification": shared_store.get("classification", {}),
            "shared_store": shared_store
        }
    
    def exec(self, prep_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行行业影响分析 - 同步方法"""
        return asyncio.run(self._exec_async(prep_data))
    
    async def _exec_async(self, prep_data: Dict[str, Any]) -> Dict[str, Any]:
        """异步执行行业影响分析"""
        news_content = prep_data.get("news_content", "")
        classification = prep_data.get("classification", {})
        
        prompt = self._build_industry_analysis_prompt(news_content, classification)
        
        try:
            async with self.llm_client as client:
                response = await client.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=800
                )
            
            # 解析行业分析结果
            industry_analysis = self._parse_industry_response(response.content)
            
            logger.info(f"行业分析完成，影响 {len(industry_analysis.get('affected_industries', []))} 个行业")
            
            return {
                "industry_analysis": industry_analysis,
                "action": "relate_stocks"
            }
        
        except Exception as e:
            logger.error(f"行业分析失败: {e}")
            return {
                "error": str(e),
                "action": "error"
            }
    
    def post(self, shared_store: Dict[str, Any], prep_data: Dict[str, Any], exec_result: Dict[str, Any]) -> str:
        """后处理 - 保存结果到共享存储并返回下一步动作"""
        if "industry_analysis" in exec_result:
            shared_store["industry_analysis"] = exec_result["industry_analysis"]
        
        if "error" in exec_result:
            shared_store["error"] = exec_result["error"]
        
        return exec_result.get("action", "error")
    
    def _build_industry_analysis_prompt(self, news_content: str, classification: Dict) -> str:
        """构建行业分析Prompt"""
        return f"""你是一个资深的行业分析师。请分析新闻对各行业的影响：

新闻内容：
{news_content[:2000]}

新闻分类信息：
- 类型：{classification.get('news_type', '未知')}
- 重要性：{classification.get('importance_score', 0)}分
- 涉及实体：{', '.join(classification.get('entities', []))}
- 情感倾向：{classification.get('sentiment', '中性')}

请分析：
1. 主要影响行业：最多3个最相关的行业
2. 影响类型：[利好/利空/中性]
3. 影响程度：1-10分（10分影响最大）
4. 影响时间：[短期/中期/长期]
5. 传导路径：影响如何传递到该行业

中国股市主要行业分类：
- 科技：人工智能、芯片半导体、软件、互联网、通信
- 金融：银行、保险、证券、支付、金融科技
- 医药：生物医药、医疗器械、化学制药、中药
- 消费：食品饮料、家电、零售、汽车、教育
- 制造：机械设备、化工、建材、钢铁、有色金属
- 能源：石油石化、煤炭、新能源、电力、环保
- 地产：房地产开发、建筑工程、装修装饰
- 农业：农林牧渔、种业、农业机械

返回JSON格式：
{{
  "affected_industries": [
    {{
      "industry": "行业名称",
      "impact_type": "利好/利空/中性",
      "impact_degree": 分数,
      "time_horizon": "短期/中期/长期",
      "reasoning": "影响逻辑说明"
    }}
  ],
  "overall_market_impact": "对整体市场的影响评估"
}}"""
    
    def _parse_industry_response(self, response_text: str) -> Dict[str, Any]:
        """解析行业分析响应"""
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                raise ValueError("无法找到有效的JSON内容")
        
        except Exception as e:
            logger.error(f"解析行业分析结果失败: {e}")
            return {
                "affected_industries": [],
                "overall_market_impact": "影响未明"
            }

class StockRelatorAgent(Node):
    """股票关联器Agent - 根据行业分析获取相关股票"""
    
    def __init__(self, llm_client: QwenLLMClient):
        super().__init__()
        self.llm_client = llm_client
        self.stock_factory = StockDataFactory()
    
    def prep(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """准备股票关联分析所需的数据"""
        return {
            "industry_analysis": shared_store.get("industry_analysis", {}),
            "shared_store": shared_store
        }
    
    def exec(self, prep_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行股票关联分析 - 同步方法"""
        return asyncio.run(self._exec_async(prep_data))
    
    async def _exec_async(self, prep_data: Dict[str, Any]) -> Dict[str, Any]:
        """异步执行股票关联分析"""
        industry_analysis = prep_data.get("industry_analysis", {})
        affected_industries = industry_analysis.get("affected_industries", [])
        
        if not affected_industries:
            logger.warning("没有找到受影响的行业，跳过股票关联")
            return {
                "related_stocks": [],
                "action": "generate_advice"
            }
        
        try:
            related_stocks = []
            
            # 为每个受影响的行业查找相关股票
            for industry_info in affected_industries:
                industry_name = industry_info.get("industry", "")
                impact_type = industry_info.get("impact_type", "中性")
                impact_degree = industry_info.get("impact_degree", 5)
                
                # 使用LLM推荐该行业的代表性股票
                stocks = await self._get_industry_stocks(industry_name, impact_type, impact_degree)
                related_stocks.extend(stocks)
            
            # 去重并按影响程度排序
            unique_stocks = self._deduplicate_and_rank_stocks(related_stocks)
            
            logger.info(f"股票关联完成，找到 {len(unique_stocks)} 只相关股票")
            
            return {
                "related_stocks": unique_stocks,
                "action": "generate_advice"
            }
        
        except Exception as e:
            logger.error(f"股票关联失败: {e}")
            return {
                "error": str(e),
                "action": "error"
            }
    
    def post(self, shared_store: Dict[str, Any], prep_data: Dict[str, Any], exec_result: Dict[str, Any]) -> str:
        """后处理 - 保存结果到共享存储并返回下一步动作"""
        if "related_stocks" in exec_result:
            shared_store["related_stocks"] = exec_result["related_stocks"]
        
        if "error" in exec_result:
            shared_store["error"] = exec_result["error"]
        
        return exec_result.get("action", "error")
    
    async def _get_industry_stocks(self, industry: str, impact_type: str, impact_degree: int) -> List[Dict]:
        """获取特定行业的代表性股票"""
        prompt = f"""请推荐{industry}行业中最具代表性的股票（中国A股市场）：

行业：{industry}
影响类型：{impact_type}
影响程度：{impact_degree}分

请推荐3-5只该行业的龙头股票，包括：
1. 股票代码（6位数字）
2. 股票名称
3. 选择理由（为什么是行业代表）
4. 关联度评分（1-10分）

返回JSON格式：
{{
  "stocks": [
    {{
      "code": "000001",
      "name": "平安银行", 
      "reason": "选择理由",
      "relevance_score": 9
    }}
  ]
}}

注意：
- 只推荐真实存在的A股股票
- 股票代码必须是6位数字格式
- 优先推荐市值较大的龙头企业"""

        try:
            async with self.llm_client as client:
                response = await client.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_tokens=600
                )
            
            result = self._parse_stocks_response(response.content)
            
            # 为每只股票添加行业信息
            stocks = result.get("stocks", [])
            for stock in stocks:
                stock["industry"] = industry
                stock["impact_type"] = impact_type
                stock["impact_degree"] = impact_degree
            
            return stocks
        
        except Exception as e:
            logger.error(f"获取{industry}行业股票失败: {e}")
            return []
    
    def _parse_stocks_response(self, response_text: str) -> Dict[str, Any]:
        """解析股票推荐响应"""
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                raise ValueError("无法找到有效的JSON内容")
        
        except Exception as e:
            logger.error(f"解析股票推荐失败: {e}")
            return {"stocks": []}
    
    def _deduplicate_and_rank_stocks(self, stocks: List[Dict]) -> List[Dict]:
        """去重并按影响程度排序股票"""
        # 按股票代码去重
        unique_stocks = {}
        for stock in stocks:
            code = stock.get("code", "")
            if code and (code not in unique_stocks or 
                        stock.get("impact_degree", 0) > unique_stocks[code].get("impact_degree", 0)):
                unique_stocks[code] = stock
        
        # 按影响程度和关联度排序
        sorted_stocks = sorted(
            unique_stocks.values(),
            key=lambda x: (x.get("impact_degree", 0) * x.get("relevance_score", 0)),
            reverse=True
        )
        
        # 限制返回数量
        return sorted_stocks[:10]

class InvestmentAdvisorAgent(Node):
    """投资建议Agent - 综合分析并提供最终投资建议"""
    
    def __init__(self, llm_client: QwenLLMClient):
        super().__init__()
        self.llm_client = llm_client
    
    def prep(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """准备投资建议生成所需的数据"""
        return {
            "classification": shared_store.get("classification", {}),
            "industry_analysis": shared_store.get("industry_analysis", {}),
            "related_stocks": shared_store.get("related_stocks", []),
            "shared_store": shared_store
        }
    
    def exec(self, prep_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成投资建议 - 同步方法"""
        return asyncio.run(self._exec_async(prep_data))
    
    async def _exec_async(self, prep_data: Dict[str, Any]) -> Dict[str, Any]:
        """异步生成投资建议"""
        classification = prep_data.get("classification", {})
        industry_analysis = prep_data.get("industry_analysis", {})
        related_stocks = prep_data.get("related_stocks", [])
        
        prompt = self._build_investment_advice_prompt(
            classification, industry_analysis, related_stocks
        )
        
        try:
            async with self.llm_client as client:
                response = await client.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,
                    max_tokens=1000
                )
            
            # 解析投资建议
            investment_advice = self._parse_advice_response(response.content)
            
            logger.info("投资建议生成完成")
            
            return {
                "investment_advice": investment_advice,
                "action": "done"
            }
        
        except Exception as e:
            logger.error(f"生成投资建议失败: {e}")
            return {
                "error": str(e),
                "action": "error"
            }
    
    def post(self, shared_store: Dict[str, Any], prep_data: Dict[str, Any], exec_result: Dict[str, Any]) -> str:
        """后处理 - 保存结果到共享存储并返回下一步动作"""
        if "investment_advice" in exec_result:
            shared_store["investment_advice"] = exec_result["investment_advice"]
        
        if "error" in exec_result:
            shared_store["error"] = exec_result["error"]
        
        return exec_result.get("action", "done")
    
    def _build_investment_advice_prompt(self, classification: Dict, 
                                      industry_analysis: Dict, 
                                      related_stocks: List[Dict]) -> str:
        """构建投资建议Prompt"""
        stocks_info = "\n".join([
            f"- {stock.get('code', '')} {stock.get('name', '')}: {stock.get('reason', '')}"
            for stock in related_stocks[:5]
        ])
        
        return f"""你是一位资深的投资顾问。请基于以下分析结果提供专业的投资建议：

新闻分类：
- 类型：{classification.get('news_type', '未知')}
- 重要性：{classification.get('importance_score', 0)}分
- 情感倾向：{classification.get('sentiment', '中性')}

行业影响分析：
{json.dumps(industry_analysis, ensure_ascii=False, indent=2)}

相关股票：
{stocks_info}

请提供：
1. 投资建议：[买入/持有/卖出/观望]
2. 投资逻辑：详细说明投资理由
3. 风险评估：主要风险点和注意事项
4. 时间建议：[短期/中期/长期]持有建议
5. 仓位建议：建议的仓位比例
6. 止损建议：风险控制措施
7. 信心指数：1-10分（对这个建议的信心程度）

返回JSON格式：
{{
  "recommendation": "买入/持有/卖出/观望",
  "rationale": "投资逻辑详细说明",
  "risk_assessment": "风险评估内容",
  "time_horizon": "短期/中期/长期",
  "position_size": "仓位建议",
  "stop_loss": "止损建议",
  "confidence_level": 分数,
  "key_factors": ["关键因素1", "关键因素2"],
  "alternative_scenarios": "其他可能情况分析"
}}

注意：
- 建议要具体可操作
- 必须包含风险提示
- 考虑当前市场环境
- 提供客观理性的分析"""
    
    def _parse_advice_response(self, response_text: str) -> Dict[str, Any]:
        """解析投资建议响应"""
        try:
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                raise ValueError("无法找到有效的JSON内容")
        
        except Exception as e:
            logger.error(f"解析投资建议失败: {e}")
            return {
                "recommendation": "观望",
                "rationale": "分析结果解析失败",
                "risk_assessment": "存在不确定性",
                "time_horizon": "短期",
                "position_size": "谨慎参与",
                "stop_loss": "及时止损",
                "confidence_level": 3,
                "key_factors": [],
                "alternative_scenarios": "需要进一步分析"
            }

class NewsAnalysisFlow:
    """新闻分析流水线主类"""
    
    def __init__(self, llm_client: QwenLLMClient):
        """
        初始化新闻分析流水线
        
        Args:
            llm_client: 千问LLM客户端
        """
        self.llm_client = llm_client
        
        # 初始化各个Agent
        self.classifier_agent = NewsClassifierAgent(self.llm_client)
        self.industry_agent = IndustryAnalyzerAgent(self.llm_client)
        self.stock_agent = StockRelatorAgent(self.llm_client)
        self.advisor_agent = InvestmentAdvisorAgent(self.llm_client)
        
        # 构建PocketFlow流程
        self.flow = self._build_flow()
    
    def _build_flow(self) -> Flow:
        """构建PocketFlow工作流程"""
        # 创建Agent实例
        self.classifier_agent = NewsClassifierAgent(self.llm_client)
        self.industry_agent = IndustryAnalyzerAgent(self.llm_client)
        self.stock_agent = StockRelatorAgent(self.llm_client)
        self.advisor_agent = InvestmentAdvisorAgent(self.llm_client)
        
        # 设置节点连接关系 - 根据action决定下一步
        # PocketFlow使用字典方式定义路径规则
        self.classifier_agent.successors = {
            "analyze_industry": self.industry_agent,
            "skip": None,  # 跳过分析
            "error": None  # 错误终止
        }
        
        self.industry_agent.successors = {
            "relate_stocks": self.stock_agent,
            "error": None
        }
        
        self.stock_agent.successors = {
            "generate_advice": self.advisor_agent,
            "error": None
        }
        
        self.advisor_agent.successors = {
            "done": None,  # 流程完成
            "error": None
        }
        
        # 创建Flow，从分类器开始
        flow = Flow(start=self.classifier_agent)
        
        return flow
    
    def analyze_news(self, news_content: str, news_id: str = None) -> NewsAnalysisResult:
        """
        分析单条新闻
        
        Args:
            news_content: 新闻内容
            news_id: 新闻ID（可选）
            
        Returns:
            新闻分析结果
        """
        start_time = datetime.now()
        news_id = news_id or f"news_{int(start_time.timestamp())}"
        
        # 初始化共享存储
        shared_store = {
            "news_content": news_content,
            "news_id": news_id,
            "start_time": start_time
        }
        
        try:
            # 执行流水线
            self.flow.run(shared_store)
            
            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 计算信心评分
            confidence_score = self._calculate_confidence_score(shared_store)
            
            # 构建结果对象
            result = NewsAnalysisResult(
                news_id=news_id,
                news_content=news_content,
                classification=shared_store.get("classification", {}),
                industry_analysis=shared_store.get("industry_analysis", {}),
                related_stocks=shared_store.get("related_stocks", []),
                investment_advice=shared_store.get("investment_advice", {}),
                analysis_time=start_time,
                confidence_score=confidence_score,
                processing_time=processing_time
            )
            
            logger.info(f"新闻分析完成: {news_id}, 耗时: {processing_time:.2f}秒")
            return result
        
        except Exception as e:
            logger.error(f"新闻分析流水线执行失败: {e}")
            # 返回错误结果
            return NewsAnalysisResult(
                news_id=news_id,
                news_content=news_content,
                classification={},
                industry_analysis={},
                related_stocks=[],
                investment_advice={"recommendation": "观望", "rationale": f"分析失败: {str(e)}"},
                analysis_time=start_time,
                confidence_score=0.0,
                processing_time=(datetime.now() - start_time).total_seconds()
            )
    
    def _calculate_confidence_score(self, shared_store: Dict[str, Any]) -> float:
        """计算分析结果的信心评分"""
        try:
            # 基础分数
            base_score = 0.5
            
            # 分类质量评分
            classification = shared_store.get("classification", {})
            if classification.get("importance_score", 0) >= 7:
                base_score += 0.2
            
            # 行业分析质量评分
            industry_analysis = shared_store.get("industry_analysis", {})
            affected_industries = industry_analysis.get("affected_industries", [])
            if len(affected_industries) > 0:
                avg_impact = sum(ind.get("impact_degree", 0) for ind in affected_industries) / len(affected_industries)
                if avg_impact >= 7:
                    base_score += 0.2
            
            # 股票关联质量评分
            related_stocks = shared_store.get("related_stocks", [])
            if len(related_stocks) >= 3:
                base_score += 0.1
            
            # 投资建议质量评分
            investment_advice = shared_store.get("investment_advice", {})
            advice_confidence = investment_advice.get("confidence_level", 0)
            if advice_confidence >= 7:
                base_score += 0.2
            
            return min(1.0, base_score)
        
        except Exception:
            return 0.5

# 便捷函数
def analyze_single_news(news_content: str, news_id: str = None) -> NewsAnalysisResult:
    """
    快速分析单条新闻的便捷函数
    
    Args:
        news_content: 新闻内容
        news_id: 新闻ID（可选）
        
    Returns:
        新闻分析结果
    """
    flow = NewsAnalysisFlow()
    return flow.analyze_news(news_content, news_id) 