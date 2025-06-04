#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
股票分析节点

分析股票相关信息并获取高评分股票推荐
"""

import asyncio
import logging
from typing import Dict, Any, List
from ...interfaces.node_interface import BaseAnalysisNode
from ....data_providers.stock_data_factory import StockDataFactory
from ....handler.ticker_handler import TickerHandler
from ....data_providers.akshare_industry_provider import get_industry_stocks_from_akshare

logger = logging.getLogger(__name__)

class StockAnalyzerNode(BaseAnalysisNode):
    """增强版股票分析器Agent - 集成实时评分和智能筛选"""
    
    def __init__(self, llm_client, max_industries: int = 3, top_stocks_per_industry: int = 10):
        super().__init__()
        self.description = "股票分析和高评分股票筛选节点"
        self.llm_client = llm_client
        self.max_industries = max_industries
        self.top_stocks_per_industry = top_stocks_per_industry
        self.ticker_handler = TickerHandler()
        self.stock_data_factory = StockDataFactory()
    
    def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行股票分析"""
        return self.exec(input_data)
    
    def prep(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """准备股票分析所需的数据"""
        return {
            "mentioned_stocks": shared_store.get("mentioned_stocks", []),
            "analysis_type": shared_store.get("analysis_type"),
            "classification": shared_store.get("classification", {}),
            "context_info": shared_store.get("context_info", {}),
            "article": shared_store.get("article"),
            "shared_store": shared_store
        }
    
    def exec(self, prep_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行增强股票分析 - 同步方法"""
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
        """异步执行增强股票分析"""
        analysis_type = prep_data.get("analysis_type")
        mentioned_stocks = prep_data.get("mentioned_stocks", [])
        classification = prep_data.get("classification", {})
        
        if analysis_type == "stock_specific":
            logger.info(f"🔍 执行个股分析路径，股票数量: {len(mentioned_stocks)}")
            
            # 🔥 个股分析路径：获取具体股票的实时评分
            analyzed_stocks = await self._analyze_specific_stocks_with_scores(mentioned_stocks)
            industry_analysis = await self._derive_industry_from_stocks(analyzed_stocks)
            
            return {
                "industry_analysis": industry_analysis,
                "related_stocks": analyzed_stocks,
                "analysis_approach": "stock_specific",
                "stock_count": len(analyzed_stocks)
            }
            
        else:  # industry_focused
            logger.info("🏭 执行行业分析路径")
            
            # 🔥 行业分析路径：识别行业后获取高评分股票
            industry_analysis = await self._analyze_industries_from_news(prep_data)
            related_stocks = await self._get_top_rated_stocks_by_industries(industry_analysis)
            
            return {
                "industry_analysis": industry_analysis,
                "related_stocks": related_stocks,
                "analysis_approach": "industry_focused", 
                "stock_count": len(related_stocks)
            }

    async def _analyze_specific_stocks_with_scores(self, mentioned_stocks: List[Dict]) -> List[Dict[str, Any]]:
        """🔥 分析具体股票并获取实时评分"""
        analyzed_stocks = []
        
        for stock in mentioned_stocks:
            try:
                stock_code = stock["code"]
                stock_name = stock["name"]
                
                # 获取30天的股票数据和评分
                ticker_data = await self.ticker_handler.get_ticker_data(stock_code, days=30)
                
                if ticker_data:
                    # 计算评分统计
                    scores = [data.get("score", 0) for data in ticker_data if data.get("score")]
                    
                    if scores:
                        current_score = scores[-1] if scores else 0  # 最新评分
                        avg_score = sum(scores) / len(scores)  # 平均评分
                        score_trend = self._calculate_score_trend(scores)  # 评分趋势
                        
                        analyzed_stocks.append({
                            "code": stock_code,
                            "name": stock_name,
                            "market": stock.get("market", "CN"),
                            "confidence": stock.get("confidence", 0.8),
                            "current_score": current_score,
                            "avg_score_30d": round(avg_score, 2),
                            "score_trend": score_trend,
                            "score_count": len(scores),
                            "ticker_id": stock.get("ticker_id"),
                            "group_id": stock.get("group_id"),
                            "analysis_source": "mentioned_direct"
                        })
                        
                        logger.info(f"📊 {stock_name}({stock_code}): 当前评分={current_score}, 30日均分={avg_score:.2f}, 趋势={score_trend}")
                    else:
                        # 没有评分数据，但股票存在
                        analyzed_stocks.append({
                            "code": stock_code,
                            "name": stock_name,
                            "market": stock.get("market", "CN"),
                            "confidence": stock.get("confidence", 0.8),
                            "current_score": 0,
                            "avg_score_30d": 0,
                            "score_trend": "无数据",
                            "score_count": 0,
                            "ticker_id": stock.get("ticker_id"),
                            "group_id": stock.get("group_id"),
                            "analysis_source": "mentioned_direct"
                        })
                        
                        logger.warning(f"⚠️ {stock_name}({stock_code}): 无评分数据")
                
            except Exception as e:
                logger.error(f"股票分析失败 {stock.get('name', 'N/A')}({stock.get('code', 'N/A')}): {e}")
        
        # 按当前评分排序
        analyzed_stocks.sort(key=lambda x: x["current_score"], reverse=True)
        return analyzed_stocks
    
    def _calculate_score_trend(self, scores: List[float]) -> str:
        """计算评分趋势"""
        if len(scores) < 2:
            return "数据不足"
        
        # 简单趋势计算：比较最近1/3和前1/3的平均值
        third = len(scores) // 3
        if third == 0:
            return "数据不足"
        
        recent_avg = sum(scores[-third:]) / third
        early_avg = sum(scores[:third]) / third
        
        diff = recent_avg - early_avg
        
        if diff > 0.5:
            return "上升"
        elif diff < -0.5:
            return "下降"
        else:
            return "平稳"

    async def _derive_industry_from_stocks(self, mentioned_stocks: List[Dict]) -> Dict[str, Any]:
        """从股票推导行业分析"""
        if not mentioned_stocks:
            return {"affected_industries": [], "analysis": "无具体股票信息"}
        
        # 根据股票分组信息推导行业
        group_ids = [stock.get("group_id", 0) for stock in mentioned_stocks]
        unique_groups = list(set(group_ids))
        
        # 这里可以根据group_id映射到具体行业
        # 暂时使用简化逻辑
        industry_mapping = {
            1: "银行",
            2: "证券", 
            3: "保险",
            4: "房地产",
            5: "制造业",
            6: "科技",
            7: "医药",
            8: "消费",
            9: "能源",
            10: "材料"
        }
        
        affected_industries = []
        for group_id in unique_groups:
            if group_id in industry_mapping:
                affected_industries.append({
                    "industry": industry_mapping[group_id],
                    "group_id": group_id,
                    "stock_count": len([s for s in mentioned_stocks if s.get("group_id") == group_id])
                })
        
        return {
            "affected_industries": affected_industries,
            "analysis": f"基于{len(mentioned_stocks)}只具体股票的行业分析",
            "total_stocks": len(mentioned_stocks)
        }

    async def _analyze_industries_from_news(self, prep_data: Dict[str, Any]) -> Dict[str, Any]:
        """🔥 从新闻内容分析相关行业"""
        classification = prep_data.get("classification", {})
        context_info = prep_data.get("context_info", {})
        article = prep_data.get("article")
        
        # 从分类结果提取行业信息
        classified_industries = classification.get("industry", [])
        investment_theme = classification.get("investment_theme", "")
        
        # 行业关键词映射
        industry_keywords = {
            "银行": ["银行", "降准", "存款", "贷款", "利率", "央行"],
            "科技": ["科技", "AI", "人工智能", "芯片", "半导体", "软件"],
            "医药": ["医药", "制药", "新药", "生物", "疫苗", "医疗"],
            "新能源": ["新能源", "电动车", "锂电", "光伏", "风电", "充电"],
            "房地产": ["房地产", "地产", "住房", "楼市", "房价"],
            "消费": ["消费", "零售", "电商", "食品", "饮料"],
            "制造": ["制造", "工业", "机械", "汽车", "钢铁"],
            "金融": ["金融", "证券", "保险", "基金", "信托"]
        }
        
        # 内容匹配得分
        content = f"{article.title} {article.content}" if article else ""
        industry_scores = {}
        
        for industry, keywords in industry_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in content:
                    score += 1
            industry_scores[industry] = score
        
        # 合并分类结果和关键词匹配
        affected_industries = []
        
        # 添加分类识别的行业
        for industry in classified_industries[:self.max_industries]:
            affected_industries.append({
                "industry": industry,
                "confidence": 0.8,
                "source": "llm_classification",
                "keyword_score": industry_scores.get(industry, 0)
            })
        
        # 添加关键词匹配度高的行业
        sorted_industries = sorted(industry_scores.items(), key=lambda x: x[1], reverse=True)
        for industry, score in sorted_industries[:self.max_industries]:
            if score > 0 and not any(ai["industry"] == industry for ai in affected_industries):
                affected_industries.append({
                    "industry": industry, 
                    "confidence": min(score * 0.2, 1.0),
                    "source": "keyword_matching",
                    "keyword_score": score
                })
        
        return {
            "affected_industries": affected_industries[:self.max_industries],
            "analysis": f"基于内容分析识别{len(affected_industries)}个相关行业",
            "investment_theme": investment_theme
        }

    async def _get_top_rated_stocks_by_industries(self, industry_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """🔥 根据行业获取高评分股票 - 使用AKShare真实数据"""
        affected_industries = industry_analysis.get("affected_industries", [])
        all_related_stocks = []
        
        logger.info(f"🔍 开始分析 {len(affected_industries)} 个行业的股票")
        
        for industry_info in affected_industries:
            industry = industry_info["industry"]
            confidence = industry_info.get("confidence", 0.5)
            impact_type = industry_info.get("impact_type", "positive")
            impact_degree = min(int(confidence * 10), 10)  # 转换为1-10的影响程度
            
            try:
                logger.info(f"📊 获取行业 '{industry}' 的股票 (影响度: {impact_degree}/10)")
                
                # 🔥 修复问题3: 使用真正的AKShare接口而不是硬编码映射
                industry_stocks = await get_industry_stocks_from_akshare(
                    industry=industry,
                    impact_type=impact_type, 
                    impact_degree=impact_degree
                )
                
                if not industry_stocks:
                    logger.warning(f"⚠️  行业 '{industry}' 未获取到AKShare数据，跳过")
                    continue
                
                logger.info(f"✅ 行业 '{industry}' 获取到 {len(industry_stocks)} 只候选股票")
                
                # 获取这些股票的评分数据并筛选高分股票
                high_score_stocks = []
                for stock_info in industry_stocks[:20]:  # 限制每个行业最多处理20只股票
                    stock_code = stock_info.get("code", "")
                    stock_name = stock_info.get("name", "")
                    relevance_score = stock_info.get("relevance_score", 5)
                    
                    if not stock_code:
                        continue
                        
                    try:
                        # 从AKShare获取的股票直接使用其相关性评分
                        # 这比数据库中可能过时的评分更准确
                        akshare_score = relevance_score  # AKShare提供的相关性评分
                        market_data = {
                            "latest_price": stock_info.get("latest_price", 0),
                            "change_pct": stock_info.get("change_pct", 0),
                            "market_cap": stock_info.get("market_cap", 0),
                            "turnover_rate": stock_info.get("turnover_rate", 0)
                        }
                        
                        # 只选择评分较高的股票 (AKShare相关性评分 >= 6)
                        if akshare_score >= 6.0:
                            ticker = await self.ticker_handler.get_ticker_by_code(stock_code)
                            
                            stock_data = {
                                "code": stock_code,
                                "name": stock_name,
                                "market": self._determine_market(stock_code),
                                "current_score": akshare_score,
                                "avg_recent_score": akshare_score,
                                "industry": industry,
                                "industry_confidence": confidence,
                                "analysis_source": f"akshare_{industry}",
                                "reason": stock_info.get("reason", f"{industry}板块相关"),
                                "board_name": stock_info.get("board_name", industry),
                                **market_data
                            }
                            
                            # 如果找到了ticker信息，添加ticker_id
                            if ticker:
                                stock_data.update({
                                    "ticker_id": ticker.id,
                                    "group_id": ticker.group_id
                                })
                            
                            high_score_stocks.append(stock_data)
                            logger.debug(f"📈 高分股票: {stock_name}({stock_code}) - {industry} - AKShare评分: {akshare_score}")
                        else:
                            logger.debug(f"⚪ 低分股票: {stock_name}({stock_code}) - 评分: {akshare_score} < 6.0")
                            
                    except Exception as e:
                        logger.warning(f"⚠️  处理股票 {stock_code} 失败: {e}")
                        continue
                
                all_related_stocks.extend(high_score_stocks)
                logger.info(f"✅ 行业 '{industry}' 筛选出 {len(high_score_stocks)} 只高评分股票")
                
            except Exception as e:
                logger.error(f"❌ 行业股票获取失败 {industry}: {e}")
        
        # 去重、排序和限制数量
        unique_stocks = self._deduplicate_stocks(all_related_stocks)
        
        # 按评分排序，取top 20
        top_stocks = sorted(unique_stocks, key=lambda x: x["current_score"], reverse=True)[:20]
        
        logger.info(f"🏆 从{len(affected_industries)}个行业筛选出{len(top_stocks)}只高评分股票")
        
        # 🔥 修复问题4: 如果找到0只股票，记录详细信息便于调试
        if len(top_stocks) == 0:
            logger.warning(f"⚠️  未找到高评分股票 - 调试信息:")
            logger.warning(f"   - 分析的行业: {[info['industry'] for info in affected_industries]}")
            logger.warning(f"   - 获取的原始股票总数: {len(all_related_stocks)}")
            logger.warning(f"   - 去重后股票数: {len(unique_stocks)}")
            if unique_stocks:
                max_score = max(stock["current_score"] for stock in unique_stocks)
                logger.warning(f"   - 最高评分: {max_score} (阈值: 6.0)")
        
        return top_stocks
    
    def _determine_market(self, stock_code: str) -> str:
        """确定股票市场"""
        if stock_code.startswith(('60', '68')):
            return "SH"  # 上海
        elif stock_code.startswith(('00', '30')):
            return "SZ"  # 深圳
        elif len(stock_code) == 5 and stock_code.startswith('0'):
            return "HK"  # 港股
        else:
            return "CN"  # 默认中国市场
    
    def _deduplicate_stocks(self, stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重股票列表，保留最高评分"""
        unique_stocks = {}
        
        for stock in stocks:
            code = stock["code"]
            if code not in unique_stocks or stock["current_score"] > unique_stocks[code]["current_score"]:
                unique_stocks[code] = stock
        
        return list(unique_stocks.values())

    def post(self, shared_store: Dict[str, Any], prep_data: Dict[str, Any], exec_result: Dict[str, Any]) -> str:
        """后处理：将股票分析结果存储到共享存储"""
        shared_store.update({
            "industry_analysis": exec_result.get("industry_analysis", {}),
            "related_stocks": exec_result.get("related_stocks", []),
            "analysis_approach": exec_result.get("analysis_approach", "unknown"),
            "stock_count": exec_result.get("stock_count", 0)
        })
        return "generate_advice" 