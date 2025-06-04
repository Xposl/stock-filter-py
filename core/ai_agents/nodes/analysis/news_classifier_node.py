#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
新闻分类分析节点

从新闻内容中分类新闻类型并检测相关股票
"""

import logging
import re
import os
from typing import Dict, Any, List

from dotenv import load_dotenv
from ...interfaces.node_interface import BaseAnalysisNode
from ....handler.ticker_handler import TickerHandler

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MockTickerHandler:
    """用于测试环境的Mock TickerHandler，避免数据库连接问题"""
    
    def __init__(self):
        logger.info("🧪 使用Mock TickerHandler (测试模式)")
    
    async def get_ticker_by_code(self, code: str):
        """Mock方法：返回模拟的股票信息"""
        return None
    
    async def get_ticker_data(self, code: str, days: int = 30):
        """Mock方法：返回空的评分数据"""
        return []


class NewsClassifierNode(BaseAnalysisNode):
    """新闻分类器Agent - 主要使用大模型进行智能分类"""
    
    def __init__(self, llm_client, test_mode: bool = False):
        super().__init__()
        self.description = "新闻分类和股票检测节点"
        self.llm_client = llm_client
        
        # 🔧 根据测试模式决定使用真实还是Mock的TickerHandler
        self.test_mode = test_mode or os.getenv('AI_TEST_MODE', '').lower() in ['true', '1', 'mock']
        
        if self.test_mode:
            self.ticker_handler = MockTickerHandler()
            logger.info("🧪 AI Agent运行在测试模式下")
        else:
            try:
                self.ticker_handler = TickerHandler()
                logger.info("🚀 AI Agent使用真实数据库连接")
            except Exception as e:
                logger.warning(f"⚠️ 数据库连接失败，自动切换到测试模式: {e}")
                self.ticker_handler = MockTickerHandler()
                self.test_mode = True
        
        # 🔥 简化的股票检测正则 - 只保留最可靠的模式
        self.stock_code_patterns = [
            # 中文公司名+代码格式（最可靠）
            r'([\\u4e00-\\u9fa5A-Za-z&]{2,20})[（\\(](\\d{5,6})[）\\)]',
            # 英文公司名+代码格式
            r'([A-Za-z&\\s]{3,20})[（\\(](\\d{5,6})[）\\)]',
        ]
    
    def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行新闻分类分析"""
        return self.work(input_data)
    
    def prep(self, shared_store: Dict[str, Any]) -> Dict[str, Any]:
        """准备分类所需的数据"""
        article = shared_store.get("article")
        if not article:
            return {}
        
        # 获取文章内容
        content = article.get_analysis_content()
        
        return {
            "title": article.title,
            "content": content or "",
            "article": article
        }
    
    def work(self, prepared_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行新闻分类 - 主要使用大模型"""
        title = prepared_data.get("title", "")
        content = prepared_data.get("content", "")
        article = prepared_data.get("article")
        
        # 1. 🎯 使用大模型进行新闻分类和股票检测
        llm_result = self._classify_with_llm(title, content)
        
        # 2. 🔍 简单的股票代码提取作为补充
        detected_stocks = self._extract_stock_codes(title + " " + content)
        
        # 3. 📊 整合分析结果
        analysis_type = llm_result.get("analysis_type", "industry_focused")
        confidence = llm_result.get("confidence", 0.8)
        llm_stocks = llm_result.get("mentioned_stocks", [])
        
        # 合并LLM检测和正则检测的股票
        all_stocks = self._merge_stock_results(llm_stocks, detected_stocks)
        
        logger.info(f"📊 LLM分析路径决策: {analysis_type} | 理由: {llm_result.get('reason', '大模型分析')}, 检测到{len(all_stocks)}只股票")
        
        return {
            "analysis_type": analysis_type,
            "confidence": confidence,
            "mentioned_stocks": all_stocks,
            "llm_reason": llm_result.get("reason", ""),
            "title": title,
            "content": content
        }
    
    def _classify_with_llm(self, title: str, content: str) -> Dict[str, Any]:
        """使用大模型进行新闻分类和股票检测"""
        
        # 构建分类提示词
        analysis_prompt = f"""请分析以下新闻内容，判断其类型并提取股票信息：

标题：{title}
内容：{content[:1000]}...

请按以下格式返回JSON结果：
{{
    "analysis_type": "stock_specific" 或 "industry_focused",
    "confidence": 0.0-1.0之间的置信度,
    "reason": "判断理由",
    "mentioned_stocks": [
        {{"name": "股票名称", "code": "股票代码"}}
    ]
}}

分类标准：
- stock_specific: 明确提及具体股票名称和代码的新闻
- industry_focused: 主要讨论行业、主题、政策等的新闻

请重点关注标题和内容中是否包含"公司名(代码)"格式的股票信息。"""

        try:
            # 🔥 使用正确的同步调用方法
            response = self.llm_client.chat_completions_create(
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.3,
                max_tokens=300
            )
            
            # 解析LLM响应
            response_text = response.content.strip()
            logger.info(f"🔍 LLM原始响应: {response_text[:200]}...")  # 调试日志
            
            # 尝试解析JSON
            import json
            import re
            
            # 🔥 先去除markdown代码块包装
            cleaned_text = response_text
            # 移除```json开头和```结尾
            cleaned_text = re.sub(r'^```json\s*', '', cleaned_text, flags=re.IGNORECASE)
            cleaned_text = re.sub(r'\s*```$', '', cleaned_text)
            
            # 提取JSON部分
            json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                logger.info(f"🔍 提取的JSON: {json_str[:200]}...")  # 调试日志
                result = json.loads(json_str)
                
                # 验证和标准化结果
                return {
                    "analysis_type": result.get("analysis_type", "industry_focused"),
                    "confidence": max(0.0, min(1.0, float(result.get("confidence", 0.8)))),
                    "reason": result.get("reason", "LLM分析"),
                    "mentioned_stocks": result.get("mentioned_stocks", [])
                }
            else:
                logger.warning(f"LLM返回结果无法解析为JSON，原始内容: {response_text[:500]}")
                return self._get_default_classification()
                
        except Exception as e:
            logger.error(f"LLM分类失败: {e}，使用默认分类")
            return self._get_default_classification()
    
    def _extract_stock_codes(self, text: str) -> List[Dict[str, Any]]:
        """简化的股票代码提取"""
        stocks = []
        
        for pattern in self.stock_code_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) == 2:  # (name, code)
                    name, code = match
                    stocks.append({
                        "name": name.strip(),
                        "code": code.strip(),
                        "source": "regex"
                    })
        
        # 去重
        seen_codes = set()
        unique_stocks = []
        for stock in stocks:
            if stock["code"] not in seen_codes:
                seen_codes.add(stock["code"])
                unique_stocks.append(stock)
        
        return unique_stocks
    
    def _merge_stock_results(self, llm_stocks: List[Dict], regex_stocks: List[Dict]) -> List[Dict[str, Any]]:
        """合并LLM和正则检测的股票结果"""
        merged = {}
        
        # 添加LLM检测的股票
        for stock in llm_stocks:
            code = stock.get("code", "").strip()
            if code:
                merged[code] = {
                    "name": stock.get("name", "").strip(),
                    "code": code,
                    "source": "llm"
                }
        
        # 添加正则检测的股票（如果LLM没有检测到）
        for stock in regex_stocks:
            code = stock.get("code", "").strip()
            if code and code not in merged:
                merged[code] = stock
        
        return list(merged.values())
    
    def _get_default_classification(self) -> Dict[str, Any]:
        """获取默认分类结果"""
        return {
            "analysis_type": "industry_focused",
            "confidence": 0.7,
            "reason": "默认分类（LLM分析失败）",
            "mentioned_stocks": []
        }
    
    def post(self, shared_store: Dict[str, Any], prep_data: Dict[str, Any], exec_result: Dict[str, Any]) -> str:
        """后处理：将分类结果存储到共享存储并决定下一步动作"""
        # 将分类结果保存到共享存储
        shared_store.update({
            "analysis_type": exec_result.get("analysis_type", "industry_focused"),
            "confidence": exec_result.get("confidence", 0.8),
            "mentioned_stocks": exec_result.get("mentioned_stocks", []),
            "llm_reason": exec_result.get("llm_reason", ""),
            "classification": {
                "analysis_type": exec_result.get("analysis_type", "industry_focused"),
                "confidence": exec_result.get("confidence", 0.8),
                "reason": exec_result.get("llm_reason", "")
            }
        })
        
        # 决定下一步动作
        analysis_type = exec_result.get("analysis_type", "industry_focused")
        if analysis_type == "stock_specific":
            return "analyze_stocks"
        else:
            return "analyze_industry" 