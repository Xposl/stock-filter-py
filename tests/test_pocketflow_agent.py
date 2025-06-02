#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PocketFlow Agent 测试脚本

测试基于PocketFlow框架的新闻分析AI代理功能：
1. 千问LLM客户端基础功能测试
2. 新闻分析工作流四层流水线测试
3. 模拟数据的完整端到端测试
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ai_agents.llm_clients.qwen_client import QwenLLMClient
from core.ai_agents.flow_definitions.news_analysis_flow import NewsAnalysisFlow, analyze_news_articles

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 测试用的模拟新闻数据
MOCK_NEWS_ARTICLES = [
    {
        "id": 1,
        "title": "央行降准释放流动性，银行股集体上涨",
        "content": "中国人民银行今日宣布降准0.5个百分点，向市场释放长期流动性约1万亿元。此次降准有利于银行增加放贷，支持实体经济发展。受此消息影响，银行股集体上涨，工商银行上涨3.2%，建设银行上涨2.8%。",
        "source_name": "第一财经",
        "publish_time": "2025-01-27 14:30:00",
        "url": "https://example.com/news/1",
        "status": "pending"
    },
    {
        "id": 2,
        "title": "科技股大涨，芯片板块领涨",
        "content": "今日科技股表现强劲，芯片板块领涨。中芯国际涨停，韦尔股份上涨8.5%，北方华创上涨7.2%。分析师认为，随着人工智能和5G技术的发展，芯片需求将持续增长。",
        "source_name": "东方财富",
        "publish_time": "2025-01-27 15:45:00",
        "url": "https://example.com/news/2",
        "status": "pending"
    },
    {
        "id": 3,
        "title": "房地产新政出台，开发商股价大跌",
        "content": "住建部发布房地产调控新政策，进一步加强对房地产市场的监管。受此影响，房地产开发商股价大跌，万科下跌6.8%，恒大下跌9.2%。业内人士认为，政策将对房地产行业产生深远影响。",
        "source_name": "财新",
        "publish_time": "2025-01-27 16:20:00",
        "url": "https://example.com/news/3",
        "status": "pending"
    },
    {
        "id": 4,
        "title": "新能源汽车销量创新高，比亚迪股价上涨",
        "content": "最新数据显示，1月份新能源汽车销量同比增长45%，创历史新高。比亚迪作为行业龙头，月销量突破30万辆。受此利好消息影响，比亚迪股价上涨5.6%，特斯拉上涨3.2%。",
        "source_name": "雪球",
        "publish_time": "2025-01-27 17:10:00",
        "url": "https://example.com/news/4",
        "status": "pending"
    },
    {
        "id": 5,
        "title": "美联储暗示可能加息，全球股市下跌",
        "content": "美联储主席在讲话中暗示可能在下次会议上加息，以应对通胀压力。此消息引发全球股市下跌，道琼斯指数下跌1.8%，纳斯达克下跌2.3%，A股三大指数也均收跌。",
        "source_name": "人民日报",
        "publish_time": "2025-01-27 18:00:00",
        "url": "https://example.com/news/5",
        "status": "pending"
    }
]

class PocketFlowAgentTester:
    """PocketFlow Agent 测试器"""
    
    def __init__(self):
        # 检查环境变量（可以设置模拟值用于测试）
        self.test_mode = os.getenv('AI_TEST_MODE', 'mock') == 'mock'
        self.qwen_api_key = os.getenv('QWEN_API_KEY')
        
    async def test_qwen_client_basic(self) -> bool:
        """测试千问客户端基础功能"""
        logger.info("🧪 测试千问LLM客户端基础功能...")
        
        if self.test_mode:
            logger.info("使用模拟模式测试千问客户端")
            return await self._test_qwen_mock()
        else:
            return await self._test_qwen_real()
    
    async def _test_qwen_mock(self) -> bool:
        """模拟模式测试千问客户端"""
        try:
            # 创建模拟客户端（不进行真实API调用）
            client = QwenLLMClient(api_key="mock_key")
            
            # 测试Token计算
            test_text = "这是一个测试文本，用于验证Token计算功能。"
            token_count = client.count_tokens(test_text)
            logger.info(f"✅ Token计算测试: '{test_text}' = {token_count} tokens")
            
            # 测试成本计算
            from core.ai_agents.llm_clients.qwen_client import TokenUsage
            usage = TokenUsage(
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150,
                estimated_cost=0.0
            )
            cost = client.calculate_cost(usage)
            logger.info(f"✅ 成本计算测试: {usage.total_tokens} tokens = ¥{cost:.6f}")
            
            # 测试模型信息
            model_info = await client.get_model_info()
            logger.info(f"✅ 模型信息测试: {model_info['model']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 千问客户端模拟测试失败: {e}")
            return False
    
    async def _test_qwen_real(self) -> bool:
        """真实API测试千问客户端"""
        if not self.qwen_api_key:
            logger.warning("⚠️ 未配置QWEN_API_KEY，跳过真实API测试")
            return True
        
        try:
            async with QwenLLMClient() as client:
                # 简单的连接测试
                response = await client.chat_completion([
                    {"role": "user", "content": "请回复'连接正常'"}
                ], max_tokens=10)
                
                if "连接正常" in response.content:
                    logger.info("✅ 千问API连接测试成功")
                    return True
                else:
                    logger.warning(f"⚠️ 千问API响应异常: {response.content}")
                    return False
        
        except Exception as e:
            logger.error(f"❌ 千问API连接测试失败: {e}")
            return False
    
    async def test_news_analysis_flow(self) -> bool:
        """测试新闻分析工作流"""
        logger.info("🧪 测试新闻分析工作流...")
        
        try:
            # 创建工作流实例
            if self.test_mode:
                # 模拟模式：不使用真实千问客户端
                flow = NewsAnalysisFlow(qwen_client=None)
            else:
                # 真实模式：使用千问客户端
                qwen_client = QwenLLMClient() if self.qwen_api_key else None
                flow = NewsAnalysisFlow(qwen_client=qwen_client)
            
            # 执行分析
            logger.info(f"开始分析 {len(MOCK_NEWS_ARTICLES)} 篇模拟新闻...")
            result = await flow.analyze_news(MOCK_NEWS_ARTICLES)
            
            # 验证结果结构
            self._validate_analysis_result(result)
            
            # 输出结果摘要
            self._print_analysis_summary(result)
            
            logger.info("✅ 新闻分析工作流测试成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 新闻分析工作流测试失败: {e}")
            return False
    
    def _validate_analysis_result(self, result: Dict[str, Any]):
        """验证分析结果的结构完整性"""
        required_fields = [
            "investment_advice", 
            "risk_assessment", 
            "sector_recommendations", 
            "analysis_summary"
        ]
        
        for field in required_fields:
            if field not in result:
                raise ValueError(f"分析结果缺少必需字段: {field}")
        
        # 验证投资建议结构
        advice = result["investment_advice"]
        if "action" not in advice or "reason" not in advice:
            raise ValueError("投资建议结构不完整")
        
        # 验证风险评估结构
        risk = result["risk_assessment"]
        if "level" not in risk or "score" not in risk:
            raise ValueError("风险评估结构不完整")
        
        logger.info("✅ 分析结果结构验证通过")
    
    def _print_analysis_summary(self, result: Dict[str, Any]):
        """打印分析结果摘要"""
        logger.info("📊 新闻分析结果摘要:")
        
        # 投资建议
        advice = result["investment_advice"]
        logger.info(f"  💰 投资建议: {advice['action']} ({advice.get('position_size', '未知')})")
        logger.info(f"     理由: {advice['reason']}")
        logger.info(f"     置信度: {advice.get('confidence_level', 0):.2f}")
        
        # 风险评估
        risk = result["risk_assessment"]
        logger.info(f"  ⚠️ 风险等级: {risk['level']} (评分: {risk.get('score', 0):.1f})")
        
        # 整体情感
        summary = result["analysis_summary"]
        overall = summary.get("overall_sentiment", {})
        logger.info(f"  😊 整体情感: {overall.get('label', '未知')} (评分: {overall.get('score', 0):.1f})")
        
        # 行业推荐
        sectors = result.get("sector_recommendations", [])
        if sectors:
            logger.info("  🏭 行业推荐:")
            for sector in sectors[:3]:  # 显示前3个
                logger.info(f"     {sector['sector']}: {sector['recommendation']}")
    
    async def test_convenience_function(self) -> bool:
        """测试便捷接口函数"""
        logger.info("🧪 测试便捷接口函数...")
        
        try:
            # 测试便捷分析函数
            result = await analyze_news_articles(MOCK_NEWS_ARTICLES[:2])  # 只测试前2篇
            
            if "investment_advice" in result:
                logger.info("✅ 便捷接口函数测试成功")
                return True
            else:
                logger.error("❌ 便捷接口函数返回结果不完整")
                return False
                
        except Exception as e:
            logger.error(f"❌ 便捷接口函数测试失败: {e}")
            return False
    
    async def test_performance_metrics(self) -> bool:
        """测试性能指标"""
        logger.info("🧪 测试性能指标...")
        
        try:
            start_time = datetime.now()
            
            # 执行分析
            flow = NewsAnalysisFlow()
            result = await flow.analyze_news(MOCK_NEWS_ARTICLES)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 计算性能指标
            articles_count = len(MOCK_NEWS_ARTICLES)
            avg_time_per_article = duration / articles_count
            
            logger.info(f"📈 性能指标:")
            logger.info(f"  总耗时: {duration:.2f}秒")
            logger.info(f"  处理文章数: {articles_count}篇")
            logger.info(f"  平均每篇: {avg_time_per_article:.2f}秒")
            
            # 性能要求验证（目标：单篇文章<5秒）
            if avg_time_per_article < 5.0:
                logger.info("✅ 性能指标符合要求")
                return True
            else:
                logger.warning(f"⚠️ 性能指标超出目标（目标<5秒，实际{avg_time_per_article:.2f}秒）")
                return False
                
        except Exception as e:
            logger.error(f"❌ 性能测试失败: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """运行所有测试"""
        logger.info("🚀 开始PocketFlow Agent完整测试...")
        
        test_results = {}
        
        # 1. 千问客户端基础测试
        test_results["qwen_basic"] = await self.test_qwen_client_basic()
        
        # 2. 新闻分析工作流测试
        test_results["analysis_flow"] = await self.test_news_analysis_flow()
        
        # 3. 便捷接口测试
        test_results["convenience_api"] = await self.test_convenience_function()
        
        # 4. 性能测试
        test_results["performance"] = await self.test_performance_metrics()
        
        # 汇总结果
        success_count = sum(1 for result in test_results.values() if result)
        total_count = len(test_results)
        
        logger.info(f"📊 测试完成统计:")
        logger.info(f"  ✅ 成功: {success_count}/{total_count}")
        logger.info(f"  ❌ 失败: {total_count - success_count}/{total_count}")
        
        for test_name, result in test_results.items():
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"  {test_name}: {status}")
        
        return test_results

async def main():
    """主测试函数"""
    logger.info("🎯 PocketFlow Agent测试程序启动")
    
    # 创建测试器
    tester = PocketFlowAgentTester()
    
    # 运行所有测试
    results = await tester.run_all_tests()
    
    # 判断整体测试结果
    if all(results.values()):
        logger.info("🎉 所有测试通过！PocketFlow Agent功能正常")
        return True
    else:
        logger.error("💥 部分测试失败，请检查错误信息")
        return False

if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 