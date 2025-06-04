#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
投资建议决策节点

综合分析结果生成投资建议
"""

import asyncio
import json
import logging
from typing import Dict, Any, List
from ...interfaces.node_interface import BaseDecisionNode

logger = logging.getLogger(__name__)

class InvestmentAdvisorNode(BaseDecisionNode):
    """投资建议Agent - 综合分析并提供最终投资建议"""
    
    def __init__(self, llm_client):
        super().__init__()
        self.description = "投资建议生成决策节点"
        self.llm_client = llm_client
    
    def decide(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行投资决策"""
        return self.exec(input_data)
    
    def prep(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """准备投资建议生成所需的数据"""
        return {
            "classification": shared_store.get("classification", {}),
            "industry_analysis": shared_store.get("industry_analysis", {}),
            "related_stocks": shared_store.get("related_stocks", []),
            "analysis_type": shared_store.get("analysis_type", "industry_focused"),
            "mentioned_stocks": shared_store.get("mentioned_stocks", []),
            "shared_store": shared_store
        }
    
    def exec(self, prep_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成投资建议 - 同步方法"""
        # 修复: 如果已经在事件循环中，直接返回协程让上层处理
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                # 在已运行的事件循环中，不能使用asyncio.run()
                import warnings
                warnings.warn("exec方法在运行中的事件循环中被调用，建议使用async版本", RuntimeWarning)
                return {}
        except RuntimeError:
            # 没有运行中的事件循环，可以使用asyncio.run()
            pass
        
        return asyncio.run(self._exec_async(prep_data))
    
    async def _exec_async(self, prep_data: Dict[str, Any]) -> Dict[str, Any]:
        """异步生成投资建议"""
        classification = prep_data.get("classification", {})
        industry_analysis = prep_data.get("industry_analysis", {})
        related_stocks = prep_data.get("related_stocks", [])
        analysis_type = prep_data.get("analysis_type", "industry_focused")
        mentioned_stocks = prep_data.get("mentioned_stocks", [])
        
        # 🔥 修复问题4: 性能优化 - 当找到0只股票时跳过LLM分析
        if len(related_stocks) == 0 and len(mentioned_stocks) == 0:
            logger.warning("⚡ 性能优化: 未找到任何相关股票，跳过LLM分析以节省token")
            
            # 返回标准化的空结果，避免LLM调用
            default_advice = {
                "recommendation": "观望",
                "rationale": "未找到足够的相关股票数据支撑投资决策，建议观望等待更多信息",
                "risk_assessment": "信息不足导致的不确定性风险",
                "time_horizon": "短期",
                "position_size": "暂不参与",
                "stop_loss": "N/A",
                "confidence_level": 2,
                "key_factors": ["缺乏相关股票数据", "信息不充分"],
                "alternative_scenarios": "等待更多相关新闻或数据后再评估",
                "token_saved": True,  # 标记为节省token的结果
                "analysis_skipped_reason": "无相关股票数据"
            }
            
            logger.info("💡 已返回默认观望建议，节省了LLM token消耗")
            return {
                "investment_advice": default_advice,
                "action": "done"
            }
        
        # 如果有相关股票，记录数量用于调试
        logger.info(f"📊 将分析 {len(related_stocks)} 只相关股票 + {len(mentioned_stocks)} 只提及股票")
        
        prompt = self._build_investment_advice_prompt(
            classification, industry_analysis, related_stocks, analysis_type, mentioned_stocks
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
            investment_advice["token_saved"] = False  # 标记为正常LLM分析
            
            logger.info("💰 投资建议生成完成 (使用LLM分析)")
            
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
                                      related_stocks: List[Dict],
                                      analysis_type: str,
                                      mentioned_stocks: List[Dict]) -> str:
        """构建投资建议Prompt"""
        
        # 根据分析类型调整提示内容
        if analysis_type == "stock_specific" and mentioned_stocks:
            focus_section = f"""
分析路径：个股分析 (检测到 {len(mentioned_stocks)} 只具体股票)
重点关注股票：{', '.join([f"{s['code']}({s.get('name', '')})" for s in mentioned_stocks])}
"""
            stocks_info = "\n".join([
                f"- {stock.get('code', '')} {stock.get('name', '')}: 评分{stock.get('current_score', 0)}/10 - {stock.get('analysis_source', '')}"
                for stock in related_stocks[:5]
            ])
        else:
            focus_section = f"""
分析路径：行业分析 (未检测到具体股票)
重点关注行业：{', '.join([ind.get('industry', '') for ind in industry_analysis.get('affected_industries', [])[:3]])}
"""
            stocks_info = "\n".join([
                f"- {stock.get('code', '')} {stock.get('name', '')}: 评分{stock.get('current_score', 0)}/10 - {stock.get('industry', '')}行业"
                for stock in related_stocks[:5]
            ])
        
        return f"""你是一位资深的投资顾问。请基于以下分析结果提供专业的投资建议：

{focus_section}

新闻分类：
- 类型：{classification.get('news_type', '未知')}
- 重要性：{classification.get('importance_score', 0)}分
- 情感倾向：{classification.get('sentiment', '中性')}
- 市场影响范围：{classification.get('market_scope', '未知')}

行业影响分析：
{json.dumps(industry_analysis, ensure_ascii=False, indent=2)}

推荐股票（按评分排序）：
{stocks_info}

请提供：
1. 投资建议：[买入/持有/卖出/观望]
2. 投资逻辑：详细说明投资理由（考虑分析路径特点）
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
- 区分个股分析与行业分析的不同策略
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