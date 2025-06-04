#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
新闻分析流水线 (增强版)

基于PocketFlow框架的多Agent协作新闻分析系统。
适配真实数据库结构，支持智能分析路径选择和高评分股票筛选。
"""

import json
import logging
import asyncio
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

# PocketFlow框架导入
from pocketflow import Flow, Node

# 项目内部模块导入
from ..llm_clients.qwen_client import QwenLLMClient
from ..llm_clients.silicon_flow_client import SiliconFlowClient
from ...data_providers.stock_data_factory import StockDataFactory
from ...models.news_article import NewsArticle
from ...models.news_source import NewsSource
from ..utils.akshare_industry_provider import get_industry_stocks_from_akshare
from ...handler.ticker_handler import TickerHandler

logger = logging.getLogger(__name__)

@dataclass
class EnhancedNewsAnalysisResult:
    """增强版新闻分析结果"""
    news_id: str
    article: NewsArticle  # 使用真实的NewsArticle对象
    analysis_type: str  # "stock_specific" 或 "industry_focused" 
    mentioned_stocks: List[Dict[str, Any]]  # 新闻中提到的具体股票
    classification: Dict[str, Any]
    industry_analysis: Dict[str, Any]
    related_stocks: List[Dict[str, Any]]  # 高评分相关股票
    investment_advice: Dict[str, Any]
    analysis_time: datetime
    confidence_score: float
    processing_time: float

class EnhancedNewsClassifierAgent(Node):
    """增强版新闻分类器Agent - 识别具体股票提及并决定分析路径"""
    
    def __init__(self, llm_client: QwenLLMClient):
        super().__init__()
        self.llm_client = llm_client
        self.ticker_handler = TickerHandler()
        
        # 🔥 增强的股票匹配模式 - 优化匹配精度
        self.stock_patterns = [
            # 🔥 修复：标准格式：股票名(代码) - 提高优先级和准确性
            r'([\u4e00-\u9fa5A-Za-z&]{2,15})[（\(](\d{6})[）\)]',  # 中文名称(6位代码)
            # 🔥 修复：港股格式：股票名(05位代码) - 支持0开头的5位代码
            r'([\u4e00-\u9fa5A-Za-z&]{2,15})[（\(](0\d{4})[）\)]',  # 港股代码
            # 股票名+空格+代码格式
            r'([\u4e00-\u9fa5A-Za-z&]{2,15})\s+(\d{6})',
            # 直接代码格式：SH600000, SZ000001  
            r'([SZ|SH])(\d{6})',
            # 6位数字代码（需要上下文判断）
            r'(?<![0-9])(\d{6})(?![0-9])',
            # 港股5位代码（0开头）
            r'(?<![0-9])(0\d{4})(?![0-9])',
            # 美股代码格式：大写字母组合
            r'\b([A-Z]{1,5})\b(?=.*(?:股票|公司|股价|涨|跌))',
        ]
        
        # 🔥 增强投资相关关键词
        self.investment_keywords = [
            '股票', '股价', '涨', '跌', '涨幅', '跌幅', '涨停', '跌停',
            '买入', '卖出', '持有', '建仓', '减仓', '止损', '盈利', '亏损', 
            '投资', '分析师', '评级', '目标价', '业绩', '财报', '利润',
            '营收', '市值', '市盈率', '市净率', '股息', '分红', '上涨',
            '下跌', '交易', '成交量', '换手率', '主力', '机构', '散户',
            '牛市', '熊市', '行情', '题材', '概念', '板块', '龙头'
        ]
    
    def prep(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """准备分类所需的数据"""
        article = shared_store.get("article")
        if not article:
            return {"error": "缺少NewsArticle对象"}
        
        # 🔥 使用新的get_analysis_content方法
        news_content = article.get_analysis_content()
        
        # 构建上下文信息
        context_info = {
            "source_name": article.source_name or "未知来源",
            "published_at": article.published_at.isoformat() if article.published_at else "未知时间",
            "category": article.category or "未分类",
            "importance_score": article.importance_score,
            "market_relevance_score": article.market_relevance_score,
            "sentiment_score": article.sentiment_score,
            "has_content": bool(article.content and article.content.strip())
        }
        
        return {
            "article": article,
            "news_content": news_content,
            "context_info": context_info,
            "shared_store": shared_store
        }
    
    def exec(self, prep_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行增强新闻分类 - 同步方法"""
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
        """异步执行增强新闻分类"""
        if "error" in prep_data:
            return {"error": prep_data["error"], "action": "error"}
            
        article = prep_data.get("article")
        news_content = prep_data.get("news_content", "")
        context_info = prep_data.get("context_info", {})
        
        if not news_content:
            logger.error("新闻内容为空")
            return {"error": "新闻内容为空", "action": "error"}
        
        try:
            # 1. 增强的股票提取逻辑
            mentioned_stocks = await self._extract_mentioned_stocks_enhanced(news_content, article)
            
            # 2. 投资相关性检测
            investment_relevance = self._check_investment_relevance(news_content)
            
            # 3. LLM深度分类分析
            classification = await self._classify_news_with_llm(news_content, mentioned_stocks, context_info)
            
            # 4. 🔥 智能路径决策增强
            analysis_decision = self._make_intelligent_path_decision(
                mentioned_stocks, investment_relevance, classification, context_info
            )
            
            analysis_type = analysis_decision["analysis_type"]
            action = analysis_decision["action"]
            reasoning = analysis_decision["reasoning"]
            
            logger.info(f"📊 分析路径决策: {analysis_type} | 理由: {reasoning}")
            logger.info(f"📈 检测到 {len(mentioned_stocks)} 只股票，投资相关性: {investment_relevance:.2f}")
            
            return {
                "classification": classification,
                "mentioned_stocks": mentioned_stocks,
                "analysis_type": analysis_type,
                "action": action,
                "reasoning": reasoning,
                "investment_relevance": investment_relevance,
                "context_info": context_info
            }
        
        except Exception as e:
            logger.error(f"增强新闻分类失败: {e}")
            return {
                "error": str(e),
                "action": "error"
            }
    
    async def _extract_mentioned_stocks_enhanced(self, news_content: str, article: NewsArticle) -> List[Dict[str, Any]]:
        """🔥 增强的股票提取逻辑 - 修复港股识别问题"""
        mentioned_stocks = []
        confidence_scores = {}
        
        # 🔥 方法1: 改进的正则匹配
        for i, pattern in enumerate(self.stock_patterns):
            matches = re.finditer(pattern, news_content, re.IGNORECASE)
            for match in matches:
                stock_code, stock_name = None, None
                confidence = 0.6  # 基础置信度
                
                groups = match.groups()
                if len(groups) == 2:
                    # 股票名(代码) 格式
                    name_or_market, code = groups
                    
                    # 🔥 修复港股代码识别
                    if re.match(r'0\d{4}', code):  # 港股5位代码（0开头）
                        stock_code = code
                        if re.match(r'[\u4e00-\u9fa5]', name_or_market):
                            stock_name = name_or_market
                            confidence = 0.95  # 港股名称+代码格式置信度最高
                            logger.debug(f"🎯 识别港股: {stock_name}({stock_code}), 置信度: {confidence}")
                    elif re.match(r'\d{6}', code):  # A股6位代码
                        stock_code = code
                        if re.match(r'[\u4e00-\u9fa5]', name_or_market):
                            stock_name = name_or_market
                            confidence = 0.9  # A股名称+代码格式置信度高
                            logger.debug(f"🎯 识别A股: {stock_name}({stock_code}), 置信度: {confidence}")
                    elif re.match(r'[A-Z]{2}', name_or_market) and re.match(r'\d{6}', code):
                        # SH600000 格式
                        stock_code = code
                        confidence = 0.8
                        logger.debug(f"🎯 识别市场代码: {name_or_market}{stock_code}, 置信度: {confidence}")
                elif len(groups) == 1:
                    # 单独代码格式
                    code = groups[0]
                    if re.match(r'0\d{4}', code):  # 港股代码
                        stock_code = code
                        confidence = 0.7  # 港股单独代码中等置信度
                        logger.debug(f"🎯 识别港股代码: {stock_code}, 置信度: {confidence}")
                    elif re.match(r'\d{6}', code):  # A股代码
                        stock_code = code
                        confidence = 0.5  # A股单独代码较低置信度
                        logger.debug(f"🎯 识别A股代码: {stock_code}, 置信度: {confidence}")
                
                if stock_code:
                    # 🔥 优先保留最高置信度，但记录所有匹配
                    match_key = f"{stock_code}_{i}"  # 加入模式索引避免冲突
                    if match_key not in confidence_scores or confidence > confidence_scores[match_key]:
                        confidence_scores[match_key] = confidence
                        
                    # 独立记录最佳匹配
                    if stock_code not in confidence_scores or confidence > confidence_scores[stock_code]:
                        confidence_scores[stock_code] = confidence
        
        # 🔥 方法2: 数据库验证和详细信息获取
        for stock_code, confidence in confidence_scores.items():
            # 跳过带模式索引的key
            if '_' in stock_code and not stock_code.replace('_', '').isdigit():
                continue
                
            try:
                # 🔥 修复：标准化股票代码（保持港股5位格式）
                normalized_code = self._normalize_stock_code_enhanced(stock_code)
                
                # 从数据库验证股票存在性
                ticker = await self.ticker_handler.get_ticker_by_code(normalized_code)
                if ticker:
                    # 增强置信度判断
                    enhanced_confidence = self._calculate_enhanced_confidence_v2(
                        stock_code, ticker.name, news_content, confidence
                    )
                    
                    mentioned_stocks.append({
                        "code": normalized_code,
                        "original_code": stock_code,
                        "name": ticker.name,
                        "market": self._determine_market(normalized_code),
                        "confidence": enhanced_confidence,
                        "ticker_id": ticker.id,
                        "group_id": ticker.group_id
                    })
                    
                    logger.info(f"✅ 验证股票: {ticker.name}({normalized_code}), 置信度: {enhanced_confidence:.2f}")
                else:
                    logger.debug(f"❌ 股票代码无效: {stock_code}")
                    
            except Exception as e:
                logger.warning(f"股票验证失败 {stock_code}: {e}")
        
        # 🔥 方法3: 利用预存的entities和keywords
        if article.entities:
            mentioned_stocks.extend(await self._extract_from_entities(article.entities))
        
        # 去重并排序
        unique_stocks = self._deduplicate_stocks(mentioned_stocks)
        return sorted(unique_stocks, key=lambda x: x["confidence"], reverse=True)
    
    def _normalize_stock_code_enhanced(self, code: str) -> str:
        """🔥 增强的股票代码标准化 - 正确处理港股代码"""
        # 移除可能的前缀
        code = re.sub(r'^(SH|SZ)', '', code)
        
        # 🔥 修复：港股代码保持5位格式
        if len(code) == 5 and code.startswith('0') and code.isdigit():
            return code  # 港股代码，保持5位
        elif len(code) == 6 and code.isdigit():
            return code  # A股代码，保持6位
        else:
            return code  # 保持原样，由后续验证
    
    def _calculate_enhanced_confidence_v2(self, original_code: str, stock_name: str, content: str, base_confidence: float) -> float:
        """🔥 计算增强置信度v2 - 改进算法"""
        confidence = base_confidence
        
        # 🔥 如果新闻标题中包含股票代码，大幅增加置信度
        title_section = content[:200]  # 标题和开头部分
        if original_code in title_section:
            confidence += 0.3
            logger.debug(f"标题包含代码 {original_code}，置信度+0.3")
        
        # 🔥 如果新闻中同时出现股票名称，增加置信度
        if stock_name and stock_name in content:
            confidence += 0.25
            logger.debug(f"内容包含股票名称 {stock_name}，置信度+0.25")
        
        # 🔥 如果周围有强投资相关词汇，增加置信度
        code_pos = content.find(original_code)
        if code_pos >= 0:
            surrounding_text = content[max(0, code_pos-50):code_pos+100]
            strong_keywords = ['涨超', '涨幅', '跌幅', '涨停', '跌停', '大涨', '大跌', '上涨', '下跌']
            for keyword in strong_keywords:
                if keyword in surrounding_text:
                    confidence += 0.15
                    logger.debug(f"周围包含强投资词汇 {keyword}，置信度+0.15")
                    break
            
            # 一般投资词汇
            general_keywords = ['股价', '市值', '业绩', '股票', '投资']
            for keyword in general_keywords:
                if keyword in surrounding_text:
                    confidence += 0.05
                    break
        
        # 🔥 港股代码额外加分
        if len(original_code) == 5 and original_code.startswith('0'):
            confidence += 0.1
            logger.debug(f"港股代码格式 {original_code}，置信度+0.1")
        
        return min(confidence, 1.0)  # 确保不超过1.0
    
    async def _extract_from_entities(self, entities: List[Dict]) -> List[Dict[str, Any]]:
        """从预存的实体信息中提取股票"""
        entity_stocks = []
        
        for entity in entities:
            if isinstance(entity, dict):
                entity_name = entity.get('name', '')
                entity_type = entity.get('type', '')
                
                # 如果实体类型是股票或公司
                if entity_type in ['STOCK', 'COMPANY', 'ORG'] or '股票' in entity_type:
                    # 尝试从实体名称中提取股票代码
                    code_match = re.search(r'(\d{5,6})', entity_name)
                    if code_match:
                        stock_code = code_match.group(1)
                        try:
                            ticker = await self.ticker_handler.get_ticker_by_code(stock_code)
                            if ticker:
                                entity_stocks.append({
                                    "code": stock_code,
                                    "original_code": stock_code,
                                    "name": ticker.name,
                                    "market": self._determine_market(stock_code),
                                    "confidence": 0.7,  # 来自实体识别的置信度
                                    "ticker_id": ticker.id,
                                    "group_id": ticker.group_id,
                                    "source": "entities"
                                })
                        except Exception as e:
                            logger.warning(f"实体股票验证失败 {stock_code}: {e}")
        
        return entity_stocks
    
    def _check_investment_relevance(self, content: str) -> float:
        """检测投资相关性得分"""
        relevance_score = 0.0
        total_keywords = len(self.investment_keywords)
        
        for keyword in self.investment_keywords:
            if keyword in content:
                relevance_score += 1.0
        
        # 归一化到0-1范围
        return min(relevance_score / total_keywords * 2, 1.0)  # 乘以2增加敏感度
    
    def _make_intelligent_path_decision(self, mentioned_stocks: List[Dict], 
                                      investment_relevance: float, 
                                      classification: Dict[str, Any],
                                      context_info: Dict[str, Any]) -> Dict[str, Any]:
        """🔥 智能分析路径决策"""
        
        # 决策因子
        stock_count = len(mentioned_stocks)
        avg_confidence = sum(s["confidence"] for s in mentioned_stocks) / max(stock_count, 1)
        market_relevance = context_info.get("market_relevance_score", 0)
        importance = context_info.get("importance_score", 0)
        
        # 决策逻辑
        reasoning_parts = []
        
        # 条件1: 明确提及高置信度股票
        if stock_count >= 1 and avg_confidence >= 0.7:
            reasoning_parts.append(f"检测到{stock_count}只高置信度股票(avg={avg_confidence:.2f})")
            return {
                "analysis_type": "stock_specific",
                "action": "analyze_stocks",
                "reasoning": "; ".join(reasoning_parts),
                "confidence": avg_confidence
            }
        
        # 条件2: 多只股票但置信度中等
        if stock_count >= 2 and avg_confidence >= 0.5:
            reasoning_parts.append(f"检测到{stock_count}只中等置信度股票，进行个股分析")
            return {
                "analysis_type": "stock_specific",
                "action": "analyze_stocks", 
                "reasoning": "; ".join(reasoning_parts),
                "confidence": avg_confidence
            }
        
        # 条件3: 单只股票但上下文强相关
        if stock_count == 1 and (investment_relevance >= 0.3 or market_relevance >= 0.5):
            reasoning_parts.append(f"单只股票但投资相关性高({investment_relevance:.2f})")
            return {
                "analysis_type": "stock_specific",
                "action": "analyze_stocks",
                "reasoning": "; ".join(reasoning_parts),
                "confidence": mentioned_stocks[0]["confidence"]
            }
        
        # 默认: 行业分析
        if investment_relevance >= 0.2:
            reasoning_parts.append(f"无明确个股或投资主题性内容，进行行业分析(投资相关性={investment_relevance:.2f})")
        else:
            reasoning_parts.append("通用新闻内容，进行主题行业分析")
            
        return {
            "analysis_type": "industry_focused",
            "action": "analyze_industry",
            "reasoning": "; ".join(reasoning_parts),
            "confidence": investment_relevance
        }
    
    def _deduplicate_stocks(self, stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重股票列表，保留最高置信度"""
        unique_stocks = {}
        
        for stock in stocks:
            code = stock["code"]
            if code not in unique_stocks or stock["confidence"] > unique_stocks[code]["confidence"]:
                unique_stocks[code] = stock
        
        return list(unique_stocks.values())

    def _determine_market(self, stock_code: str) -> str:
        """根据股票代码确定市场"""
        if stock_code.startswith(('60', '68')):
            return "SH"  # 上海
        elif stock_code.startswith(('00', '30')):
            return "SZ"  # 深圳
        else:
            return "CN"  # 默认中国市场

    async def _classify_news_with_llm(self, news_content: str, mentioned_stocks: List[Dict], context_info: Dict[str, Any]) -> Dict[str, Any]:
        """使用LLM进行新闻分类"""
        prompt = self._build_enhanced_classification_prompt(news_content, mentioned_stocks, context_info)
        
        try:
            async with self.llm_client as client:
                response = await client.chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=500
                )
            
            return self._parse_classification_response(response.content)
        
        except Exception as e:
            logger.error(f"LLM分类失败: {e}")
            return self._get_default_classification()
    
    def _build_enhanced_classification_prompt(self, news_content: str, mentioned_stocks: List[Dict], context_info: Dict[str, Any]) -> str:
        """构建增强版新闻分类Prompt"""
        stock_info = ""
        if mentioned_stocks:
            stock_list = [f"{s['name']}({s['code']})" for s in mentioned_stocks[:5]]
            stock_info = f"\n相关股票: {', '.join(stock_list)}"
        
        # 增加上下文信息
        context_str = ""
        if context_info:
            source = context_info.get("source_name", "")
            category = context_info.get("category", "")
            if source:
                context_str += f"\n新闻来源: {source}"
            if category:
                context_str += f"\n文章分类: {category}"
        
        prompt = f"""请分析以下新闻内容的投资价值和市场影响：

{news_content}{stock_info}{context_str}

请以JSON格式回复，包含以下字段：
{{
    "industry": ["相关行业1", "相关行业2"],
    "sentiment": "正面|负面|中性",
    "impact_level": "高|中|低",
    "key_points": ["要点1", "要点2", "要点3"],
    "market_impact": "对市场的影响分析",
    "investment_theme": "投资主题"
}}"""
        
        return prompt
    
    def post(self, shared_store: Dict[str, Any], prep_data: Dict[str, Any], exec_result: Dict[str, Any]) -> str:
        """后处理：将分类结果存储到共享存储"""
        if "error" not in exec_result:
            shared_store.update({
                "classification": exec_result.get("classification", {}),
                "mentioned_stocks": exec_result.get("mentioned_stocks", []),
                "analysis_type": exec_result.get("analysis_type"),
                "reasoning": exec_result.get("reasoning", ""),
                "investment_relevance": exec_result.get("investment_relevance", 0.0),
                "context_info": exec_result.get("context_info", {})
            })
            return exec_result.get("action", "error")
        else:
            shared_store["error"] = exec_result["error"]
            return "error"
    
    def _parse_classification_response(self, response_text: str) -> Dict[str, Any]:
        """解析LLM分类响应"""
        try:
            # 尝试提取JSON内容
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                return self._get_default_classification()
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"分类响应解析失败: {e}, 使用默认分类")
            return self._get_default_classification()
    
    def _get_default_classification(self) -> Dict[str, Any]:
        """获取默认分类结果"""
        return {
            "industry": ["综合"],
            "sentiment": "中性",
            "impact_level": "中",
            "key_points": ["待分析"],
            "market_impact": "市场影响待评估",
            "investment_theme": "综合投资主题"
        }

class EnhancedStockAnalyzerAgent(Node):
    """增强版股票分析器Agent - 集成实时评分和智能筛选"""
    
    def __init__(self, llm_client: QwenLLMClient, max_industries: int = 3, top_stocks_per_industry: int = 10):
        super().__init__()
        self.llm_client = llm_client
        self.max_industries = max_industries
        self.top_stocks_per_industry = top_stocks_per_industry
        self.ticker_handler = TickerHandler()
        self.stock_data_factory = StockDataFactory()
    
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

    async def _get_stocks_by_industry_name(self, industry_name: str) -> List[str]:
        """根据行业名称获取股票代码列表 - 已弃用，使用AKShare接口"""
        logger.warning(f"⚠️  _get_stocks_by_industry_name已弃用，应使用AKShare接口")
        # 保留作为备用，但不应该被调用
        industry_stock_mapping = {
            "银行": ["600000", "600036", "600016", "000001", "002142"],
            "科技": ["000858", "300059", "002415", "300496", "600570"],
            "医药": ["000661", "002007", "300003", "600276", "002821"],
            "新能源": ["002594", "300750", "002460", "688599", "300274"], 
            "消费": ["000858", "600519", "000568", "002304", "600887"],
            "制造": ["000002", "600519", "000858", "002027", "600031"],
            "金融": ["600000", "600030", "000002", "601318", "601166"]
        }
        return industry_stock_mapping.get(industry_name, [])
    
    def _determine_market(self, stock_code: str) -> str:
        """确定股票市场"""
        if stock_code.startswith(('60', '68')):
            return "SH"  # 上海
        elif stock_code.startswith(('00', '30')):
            return "SZ"  # 深圳
        else:
            return "CN"  # 默认
    
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
        self.classifier_agent = EnhancedNewsClassifierAgent(self.llm_client)
        self.stock_analyzer_agent = EnhancedStockAnalyzerAgent(self.llm_client)
        self.advisor_agent = InvestmentAdvisorAgent(self.llm_client)
    
    def analyze_news_with_article(self, article: NewsArticle) -> EnhancedNewsAnalysisResult:
        """
        分析NewsArticle对象
        
        Args:
            article: NewsArticle模型对象
            
        Returns:
            增强版新闻分析结果
        """
        # 检查是否在运行中的事件循环中
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                # 在运行中的事件循环中，使用同步调用异步方法的方式
                import concurrent.futures
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.analyze_news_with_article_async(article))
                    return future.result()
        except RuntimeError:
            # 没有运行中的事件循环，可以直接使用asyncio.run
            pass
        
        return asyncio.run(self.analyze_news_with_article_async(article))
    
    async def analyze_news_with_article_async(self, article: NewsArticle) -> EnhancedNewsAnalysisResult:
        """
        分析NewsArticle对象 - 异步版本
        
        Args:
            article: NewsArticle模型对象
            
        Returns:
            增强版新闻分析结果
        """
        start_time = datetime.now()
        
        # 初始化共享存储，传入真实的NewsArticle对象
        shared_store = {
            "article": article,
            "start_time": start_time
        }
        
        try:
            # 第一步：增强版新闻分类
            classifier_prep = self.classifier_agent.prep(shared_store)
            classifier_result = await self.classifier_agent._exec_async(classifier_prep)  # 直接调用异步方法
            action = self.classifier_agent.post(shared_store, classifier_prep, classifier_result)
            
            if action == "error":
                raise Exception(f"分类失败: {shared_store.get('error', '未知错误')}")
            
            # 第二步：根据分析类型执行股票分析
            if action in ["analyze_stocks", "analyze_industry"]:
                stock_prep = self.stock_analyzer_agent.prep(shared_store)
                stock_result = await self.stock_analyzer_agent._exec_async(stock_prep)  # 直接调用异步方法
                action = self.stock_analyzer_agent.post(shared_store, stock_prep, stock_result)
                
                if action == "error":
                    raise Exception(f"股票分析失败: {shared_store.get('error', '未知错误')}")
            
            # 第三步：生成投资建议
            if action == "generate_advice":
                advisor_prep = self.advisor_agent.prep(shared_store)
                advisor_result = await self.advisor_agent._exec_async(advisor_prep)  # 直接调用异步方法
                self.advisor_agent.post(shared_store, advisor_prep, advisor_result)
            
            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 计算信心评分
            confidence_score = self._calculate_confidence_score(shared_store)
            
            # 构建结果对象
            result = EnhancedNewsAnalysisResult(
                news_id=str(article.id),
                article=article,
                analysis_type=shared_store.get("analysis_type", "industry_focused"),
                mentioned_stocks=shared_store.get("mentioned_stocks", []),
                classification=shared_store.get("classification", {}),
                industry_analysis=shared_store.get("industry_analysis", {}),
                related_stocks=shared_store.get("related_stocks", []),
                investment_advice=shared_store.get("investment_advice", {}),
                analysis_time=start_time,
                confidence_score=confidence_score,
                processing_time=processing_time
            )
            
            logger.info(f"新闻分析完成: {article.id}, 耗时: {processing_time:.2f}秒")
            return result
        
        except Exception as e:
            logger.error(f"新闻分析流水线执行失败: {e}")
            # 返回错误结果
            return EnhancedNewsAnalysisResult(
                news_id=str(article.id),
                article=article,
                analysis_type="industry_focused",
                mentioned_stocks=[],
                classification={},
                industry_analysis={},
                related_stocks=[],
                investment_advice={"recommendation": "观望", "rationale": f"分析失败: {str(e)}"},
                analysis_time=start_time,
                confidence_score=0.0,
                processing_time=(datetime.now() - start_time).total_seconds()
            )

    def analyze_news(self, news_content: str, news_id: str = None) -> EnhancedNewsAnalysisResult:
        """
        分析单条新闻内容（向后兼容）
        
        Args:
            news_content: 新闻内容
            news_id: 新闻ID（可选）
            
        Returns:
            新闻分析结果
        """
        # 创建临时NewsArticle对象
        temp_article = NewsArticle(
            id=int(news_id) if news_id and news_id.isdigit() else 0,
            title=news_content[:100] + "..." if len(news_content) > 100 else news_content,
            url="",
            url_hash="",
            content=news_content,
            source_id=0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        return self.analyze_news_with_article(temp_article)

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
        
        except Exception as e:
            logger.error(f"计算信心评分失败: {e}")
            return 0.5

# 便捷函数
def analyze_single_news(news_content: str, news_id: str = None) -> EnhancedNewsAnalysisResult:
    """
    快速分析单条新闻的便捷函数
    
    Args:
        news_content: 新闻内容
        news_id: 新闻ID（可选）
    
    Returns:
        新闻分析结果
    """
    # 临时创建客户端
    qwen_client = QwenLLMClient()
    analysis_flow = NewsAnalysisFlow(qwen_client)
    
    return analysis_flow.analyze_news(news_content, news_id) 