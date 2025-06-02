#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
新闻分析流水线测试脚本

测试基于PocketFlow框架的多Agent协作新闻分析系统。
通过模拟新闻数据，演示从新闻内容到投资建议的完整流程。
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.ai_agents.flow_definitions.news_analysis_flow import NewsAnalysisFlow, analyze_single_news
from core.ai_agents.llm_clients.qwen_client import QwenLLMClient
from core.models.news_source import NewsSource, NewsSourceType, NewsSourceStatus

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('news_analysis_test.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

class NewsAnalysisTestSuite:
    """新闻分析测试套件"""
    
    def __init__(self):
        """初始化测试套件"""
        self.qwen_client = None
        self.analysis_flow = None
        
        # 测试新闻数据
        self.test_news_samples = [
            {
                "id": "test_001",
                "title": "央行降准释放流动性 银行板块有望受益",
                "content": """央行今日宣布全面降准0.5个百分点，释放长期资金约5000亿元。此次降准主要目的是优化银行资金结构，增强银行信贷投放能力，支持实体经济发展。

分析师认为，此次降准对银行业是明显利好，有助于降低银行资金成本，提升净息差，改善盈利能力。同时，充裕的流动性也将带动整个金融市场活跃度提升。

业内预计，大型银行和股份制银行将是本次降准的主要受益者，特别是那些资产质量优良、风控能力强的银行股值得关注。""",
                "source": "第一财经",
                "expected_impact": ["金融", "银行"],
                "expected_sentiment": "正面"
            },
            {
                "id": "test_002", 
                "title": "新能源汽车销量大增 产业链企业业绩飙升",
                "content": """最新数据显示，11月新能源汽车销量达到95万辆，同比增长39.2%，渗透率达到37.8%。头部新能源车企比亚迪、理想汽车等销量均创历史新高。

受益于销量大增，新能源汽车产业链上下游企业业绩普遍向好。动力电池龙头宁德时代第三季度净利润同比增长40%，锂电池材料企业业绩更是呈现爆发式增长。

机构认为，在政策支持和技术进步双轮驱动下，新能源汽车行业仍将保持高速增长态势，相关产业链公司具备长期投资价值。""",
                "source": "证券时报",
                "expected_impact": ["新能源", "汽车", "制造"],
                "expected_sentiment": "正面"
            },
            {
                "id": "test_003",
                "title": "房地产行业政策收紧 多家房企面临资金压力", 
                "content": """近期多地出台房地产调控政策，进一步收紧房地产市场。同时，央行和银保监会联合发布通知，要求银行严格控制房地产贷款集中度。

受政策影响，多家房地产企业面临资金链紧张问题。部分中小房企已出现债券违约风险，行业洗牌加速。评级机构纷纷下调房地产行业评级展望。

分析人士指出，房地产行业正进入深度调整期，投资者应谨慎对待房地产相关资产，关注行业风险。""",
                "source": "财经网",
                "expected_impact": ["地产", "金融"],
                "expected_sentiment": "负面"
            },
            {
                "id": "test_004",
                "title": "人工智能芯片技术突破 国产替代加速",
                "content": """国内人工智能芯片企业在GPU和AI加速芯片领域取得重大技术突破，性能指标已接近国际先进水平。多家科技公司表示将采用国产AI芯片替代进口产品。

工信部表示将加大对人工智能芯片产业的支持力度，推动产业链协同发展。相关企业有望在政策支持下实现快速发展。

券商研报认为，AI芯片国产化进程加速，将带动整个半导体产业链升级，相关上市公司迎来重大发展机遇。""",
                "source": "科技日报", 
                "expected_impact": ["科技", "芯片", "人工智能"],
                "expected_sentiment": "正面"
            },
            {
                "id": "test_005",
                "title": "生物医药公司新药获批 行业创新活力显现",
                "content": """国家药监局今日批准某生物医药公司的创新药物上市，这是今年第15个获批的1类新药。该药物针对罕见病治疗，填补了国内市场空白。

医药行业分析师认为，随着药审政策改革深化，国内医药企业创新能力不断提升，新药研发管线日益丰富。创新药企业有望迎来收获期。

机构建议关注研发实力强、管线丰富的创新药企，以及CRO、CDMO等医药服务企业的投资机会。""",
                "source": "医药经济报",
                "expected_impact": ["医药", "生物医药"],
                "expected_sentiment": "正面"
            }
        ]
    
    def setup(self):
        """初始化测试环境"""
        logger.info("🚀 初始化新闻分析测试环境...")
        
        try:
            # 初始化千问客户端
            self.qwen_client = QwenLLMClient()
            
            # 测试连接（使用同步方式）
            import asyncio
            async def test_connection():
                async with self.qwen_client as client:
                    test_response = await client.chat_completion(
                        messages=[{"role": "user", "content": "你好，请回复'连接正常'"}],
                        max_tokens=10
                    )
                    return test_response.content
            
            response_content = asyncio.run(test_connection())
            
            if "连接正常" in response_content:
                logger.info("✅ 千问客户端连接正常")
            else:
                logger.warning("⚠️ 千问客户端连接异常")
            
            # 初始化分析流水线
            self.analysis_flow = NewsAnalysisFlow(self.qwen_client)
            logger.info("✅ 新闻分析流水线初始化完成")
            
            return True
        
        except Exception as e:
            logger.error(f"❌ 测试环境初始化失败: {e}")
            return False
    
    def test_single_news_analysis(self, news_sample: Dict[str, Any]) -> Dict[str, Any]:
        """测试单条新闻分析"""
        logger.info(f"📰 开始分析新闻: {news_sample['title']}")
        
        try:
            # 执行新闻分析
            result = self.analysis_flow.analyze_news(
                news_content=f"{news_sample['title']}\n\n{news_sample['content']}",
                news_id=news_sample['id']
            )
            
            # 分析结果评估
            evaluation = self._evaluate_analysis_result(result, news_sample)
            
            logger.info(f"✅ 新闻分析完成: {news_sample['id']}, 耗时: {result.processing_time:.2f}秒")
            
            return {
                "news_id": news_sample['id'],
                "result": result,
                "evaluation": evaluation,
                "success": True
            }
        
        except Exception as e:
            logger.error(f"❌ 新闻分析失败: {news_sample['id']} - {e}")
            return {
                "news_id": news_sample['id'],
                "error": str(e),
                "success": False
            }
    
    def _evaluate_analysis_result(self, result, expected: Dict) -> Dict[str, Any]:
        """评估分析结果质量"""
        evaluation = {
            "accuracy_score": 0.0,
            "completeness_score": 0.0,
            "quality_score": 0.0,
            "details": {}
        }
        
        try:
            # 情感倾向准确性
            predicted_sentiment = result.classification.get("sentiment", "中性")
            expected_sentiment = expected.get("expected_sentiment", "中性")
            sentiment_match = predicted_sentiment == expected_sentiment
            evaluation["details"]["sentiment_match"] = sentiment_match
            
            # 行业影响准确性
            predicted_industries = [
                ind.get("industry", "") for ind in 
                result.industry_analysis.get("affected_industries", [])
            ]
            expected_industries = expected.get("expected_impact", [])
            industry_overlap = len(set(predicted_industries) & set(expected_industries))
            industry_accuracy = industry_overlap / max(len(expected_industries), 1)
            evaluation["details"]["industry_accuracy"] = industry_accuracy
            
            # 完整性评分
            has_classification = bool(result.classification)
            has_industry_analysis = bool(result.industry_analysis.get("affected_industries"))
            has_stocks = bool(result.related_stocks)
            has_advice = bool(result.investment_advice.get("recommendation"))
            
            completeness_score = sum([has_classification, has_industry_analysis, has_stocks, has_advice]) / 4
            evaluation["completeness_score"] = completeness_score
            
            # 准确性评分
            accuracy_score = (sentiment_match + industry_accuracy) / 2
            evaluation["accuracy_score"] = accuracy_score
            
            # 质量评分
            importance_score = result.classification.get("importance_score", 0) / 10
            confidence_level = result.investment_advice.get("confidence_level", 0) / 10
            quality_score = (importance_score + confidence_level + result.confidence_score) / 3
            evaluation["quality_score"] = quality_score
            
        except Exception as e:
            logger.error(f"结果评估失败: {e}")
        
        return evaluation
    
    def run_batch_test(self) -> Dict[str, Any]:
        """运行批量测试"""
        logger.info("📊 开始批量新闻分析测试...")
        
        batch_results = {
            "total_count": len(self.test_news_samples),
            "success_count": 0,
            "failed_count": 0,
            "total_time": 0.0,
            "results": []
        }
        
        start_time = datetime.now()
        
        for news_sample in self.test_news_samples:
            test_result = self.test_single_news_analysis(news_sample)
            batch_results["results"].append(test_result)
            
            if test_result["success"]:
                batch_results["success_count"] += 1
            else:
                batch_results["failed_count"] += 1
        
        batch_results["total_time"] = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"📈 批量测试完成: {batch_results['success_count']}/{batch_results['total_count']} 成功")
        
        return batch_results
    
    def print_detailed_result(self, test_result: Dict[str, Any]):
        """打印详细的测试结果"""
        if not test_result["success"]:
            print(f"❌ 分析失败: {test_result['news_id']} - {test_result['error']}")
            return
        
        result = test_result["result"]
        evaluation = test_result["evaluation"]
        
        print(f"\n📰 新闻分析结果: {result.news_id}")
        print("=" * 60)
        
        # 新闻分类
        classification = result.classification
        print(f"📊 新闻分类:")
        print(f"  类型: {classification.get('news_type', '未知')}")
        print(f"  重要性: {classification.get('importance_score', 0)}/10")
        print(f"  情感: {classification.get('sentiment', '中性')}")
        print(f"  值得分析: {classification.get('worth_analysis', False)}")
        
        # 行业影响
        industry_analysis = result.industry_analysis
        print(f"\n🏭 行业影响:")
        for industry in industry_analysis.get("affected_industries", []):
            print(f"  • {industry.get('industry', '')} - {industry.get('impact_type', '')} ({industry.get('impact_degree', 0)}/10)")
        
        # 相关股票
        print(f"\n📈 相关股票 (前5只):")
        for stock in result.related_stocks[:5]:
            print(f"  • {stock.get('code', '')} {stock.get('name', '')} - 关联度: {stock.get('relevance_score', 0)}/10")
        
        # 投资建议
        advice = result.investment_advice
        print(f"\n💰 投资建议:")
        print(f"  建议: {advice.get('recommendation', '观望')}")
        print(f"  时间: {advice.get('time_horizon', '短期')}")
        print(f"  信心: {advice.get('confidence_level', 0)}/10")
        print(f"  理由: {advice.get('rationale', '无')[:100]}...")
        
        # 评估结果
        print(f"\n📊 评估结果:")
        print(f"  准确性: {evaluation['accuracy_score']:.2f}")
        print(f"  完整性: {evaluation['completeness_score']:.2f}")
        print(f"  质量: {evaluation['quality_score']:.2f}")
        print(f"  信心评分: {result.confidence_score:.2f}")
        print(f"  处理时间: {result.processing_time:.2f}秒")
        
        print("=" * 60)
    
    def test_with_mock_news_source(self):
        """使用模拟新闻源进行测试"""
        logger.info("🔍 创建模拟新闻源进行测试...")
        
        # 创建模拟新闻源
        mock_source = NewsSource(
            id=1,
            name="测试新闻源",
            source_type=NewsSourceType.RSS,
            url="https://example.com/rss.xml",
            status=NewsSourceStatus.ACTIVE
        )
        
        logger.info(f"📄 模拟新闻源: {mock_source.name}")
        
        # 选择一个示例新闻进行详细分析
        sample_news = self.test_news_samples[0]
        
        print(f"\n🎯 详细分析示例新闻:")
        print(f"标题: {sample_news['title']}")
        print(f"来源: {sample_news['source']}")
        print("-" * 50)
        
        # 执行详细分析
        result = self.test_single_news_analysis(sample_news)
        
        # 打印详细结果
        self.print_detailed_result(result)
        
        return result

def main():
    """主函数 - 改为同步执行"""
    logger.info("🌟 新闻分析流水线测试开始")
    
    # 创建测试套件
    test_suite = NewsAnalysisTestSuite()
    
    # 初始化测试环境
    if not test_suite.setup():
        logger.error("❌ 测试环境初始化失败，退出")
        return
    
    print("\n" + "=" * 60)
    logger.info("📋 第一阶段: 单条新闻详细分析测试")
    print("=" * 60)
    
    # 执行模拟新闻源测试
    test_suite.test_with_mock_news_source()
    
    logger.info("🎉 所有测试完成！")

if __name__ == "__main__":
    main() 