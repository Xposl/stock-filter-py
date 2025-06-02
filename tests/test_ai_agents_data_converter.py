#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试 data_converter 模块

验证数据转换工具的各项功能：
- 新闻数据标准化转换
- 分析结果格式转换  
- API响应转换
- 批量处理功能
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.append('.')

from core.ai_agents.utils.data_converter import (
    NewsDataConverter,
    AnalysisResultConverter, 
    APIResponseConverter,
    DatabaseModelConverter,
    StandardNewsArticle,
    StandardAnalysisResult,
    convert_news_data,
    convert_analysis_to_api,
    convert_to_json
)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestDataConverter:
    """数据转换器测试类"""
    
    def __init__(self):
        self.news_converter = NewsDataConverter()
        self.analysis_converter = AnalysisResultConverter()
        self.api_converter = APIResponseConverter()
        self.db_converter = DatabaseModelConverter()
    
    async def test_news_conversion(self) -> bool:
        """测试新闻数据转换"""
        logger.info("🔄 测试新闻数据转换...")
        
        try:
            # 测试RSS数据转换
            rss_data = {
                "title": "某科技公司发布新产品，股价上涨8%",
                "description": "该公司今日发布革命性新产品，市场反应积极，股价盘中上涨8%达到新高。分析师认为这将推动公司未来增长。",
                "link": "https://finance.example.com/news/tech-stock-rise",
                "pubDate": "Mon, 27 Jan 2025 15:30:00 GMT",
                "author": "财经记者李明",
                "category": "科技股",
                "tags": ["科技", "新产品", "股价上涨"]
            }
            
            article = self.news_converter.convert_to_standard(
                rss_data, "rss", "财经网", 1
            )
            
            # 验证转换结果
            assert article.title == "某科技公司发布新产品，股价上涨8%"
            assert article.source_name == "财经网"
            assert article.source_id == 1
            assert article.author == "财经记者李明"
            assert article.category == "科技股"
            assert len(article.tags) > 0
            
            logger.info(f"  ✅ RSS转换成功: {article.title}")
            
            # 测试雪球数据转换
            xueqiu_data = {
                "title": "热门股票分析：AI概念股持续走强",
                "text": "多只AI概念股今日表现强劲，板块整体上涨超过5%。机构资金持续流入，看好后市发展。",
                "target": "https://xueqiu.com/status/123456",
                "created_at": 1737974400,  # Unix时间戳
                "user": "雪球分析师"
            }
            
            xq_article = self.news_converter.convert_to_standard(
                xueqiu_data, "xueqiu", "雪球", 2
            )
            
            assert xq_article.title == "热门股票分析：AI概念股持续走强"
            assert xq_article.source_name == "雪球"
            assert xq_article.author == "雪球分析师"
            
            logger.info(f"  ✅ 雪球转换成功: {xq_article.title}")
            
            # 测试批量转换
            batch_data = [rss_data, xueqiu_data]
            batch_results = self.news_converter.convert_batch(
                batch_data, "rss", "综合财经", 3
            )
            
            assert len(batch_results) == 2
            logger.info(f"  ✅ 批量转换成功: {len(batch_results)} 篇文章")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ 新闻转换测试失败: {e}")
            return False
    
    async def test_analysis_conversion(self) -> bool:
        """测试分析结果转换"""
        logger.info("🔄 测试分析结果转换...")
        
        try:
            # 模拟情感分析结果
            sentiment_result = {
                "final_sentiment_score": 7.8,
                "final_sentiment_label": "积极",
                "confidence": 0.88,
                "sentiment_breakdown": {
                    "dominant_emotion": "optimistic"
                },
                "key_indicators": {
                    "sentiment_phrases": ["股价上涨", "市场看好", "前景积极"]
                }
            }
            
            # 模拟投资分析结果  
            investment_result = {
                "investment_advice": {
                    "action": "买入",
                    "position_size": "轻仓买入 (10-20%)",
                    "time_frame": "短线 (1周-1个月)",
                    "confidence": 0.82,
                    "rationale": "新产品发布推动公司基本面改善，短期有望持续上涨",
                    "target_companies": ["科技公司A", "相关产业链公司"],
                    "investment_themes": ["AI概念", "科技创新"]
                },
                "analysis_results": [
                    {
                        "opportunity": {
                            "opportunity_type": "产品创新",
                            "industry": "科技",
                            "score": 8.5,
                            "confidence": 0.85,
                            "time_horizon": "短期",
                            "key_factors": ["技术突破", "市场需求"]
                        },
                        "risk_assessment": {
                            "risk_level": "中等",
                            "risk_score": 4.2,
                            "risk_factors": ["市场竞争", "技术风险"],
                            "mitigation_strategies": ["分散投资", "止损设置"]
                        }
                    }
                ]
            }
            
            # 转换情感分析结果
            sentiment_converted = self.analysis_converter.convert_sentiment_result(sentiment_result)
            assert sentiment_converted["sentiment_score"] == 7.8
            assert sentiment_converted["sentiment_label"] == "积极"
            assert sentiment_converted["confidence"] == 0.88
            
            logger.info(f"  ✅ 情感分析转换: 评分{sentiment_converted['sentiment_score']}, 标签{sentiment_converted['sentiment_label']}")
            
            # 转换投资分析结果
            investment_converted = self.analysis_converter.convert_investment_result(investment_result)
            assert investment_converted["investment_action"] == "买入"
            assert len(investment_converted["opportunities"]) > 0
            assert len(investment_converted["risks"]) > 0
            
            logger.info(f"  ✅ 投资分析转换: 建议{investment_converted['investment_action']}, 时间框架{investment_converted['time_frame']}")
            
            # 测试完整分析结果转换
            mock_article = StandardNewsArticle(
                id=1,
                title="测试文章",
                source_name="测试源"
            )
            
            complete_result = self.analysis_converter.convert_complete_analysis(
                mock_article, sentiment_result, investment_result, 2.5
            )
            
            assert complete_result.article_id == 1
            assert complete_result.sentiment_score == 7.8
            assert complete_result.processing_time == 2.5
            assert len(complete_result.recommendations) > 0
            
            logger.info(f"  ✅ 完整分析转换: 文章ID{complete_result.article_id}, 处理时间{complete_result.processing_time}秒")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ 分析转换测试失败: {e}")
            return False
    
    async def test_api_response_conversion(self) -> bool:
        """测试API响应转换"""
        logger.info("🔄 测试API响应转换...")
        
        try:
            # 创建模拟分析结果
            analysis_result = StandardAnalysisResult(
                article_id=123,
                sentiment_score=6.5,
                sentiment_label="偏积极",
                confidence=0.75,
                key_phrases=["技术突破", "业绩增长"],
                investment_opportunities=[
                    {
                        "type": "成长机会",
                        "industry": "科技",
                        "score": 7.8,
                        "confidence": 0.8
                    }
                ],
                risk_factors=["市场波动", "竞争加剧"],
                recommendations=[
                    {
                        "action": "买入",
                        "position": "中等仓位 (20-30%)",
                        "timeframe": "中线持有",
                        "rationale": "基本面向好"
                    }
                ],
                analysis_timestamp=datetime.now(timezone.utc),
                processing_time=3.2
            )
            
            # 转换单个结果
            api_response = self.api_converter.convert_analysis_response(analysis_result)
            
            assert api_response["status"] == "success"
            assert api_response["data"]["article_id"] == 123
            assert api_response["data"]["sentiment"]["score"] == 6.5
            assert len(api_response["data"]["investment"]["opportunities"]) > 0
            
            logger.info(f"  ✅ 单个API响应转换: 文章{api_response['data']['article_id']}, 状态{api_response['status']}")
            
            # 测试批量转换
            batch_results = [analysis_result] * 3
            batch_response = self.api_converter.convert_batch_analysis_response(
                batch_results, 9.6
            )
            
            assert batch_response["status"] == "success"
            assert len(batch_response["data"]["results"]) == 3
            assert batch_response["data"]["metadata"]["total_articles"] == 3
            assert batch_response["data"]["metadata"]["total_processing_time"] == 9.6
            assert "summary" in batch_response["data"]
            
            logger.info(f"  ✅ 批量API响应转换: {len(batch_response['data']['results'])} 条结果")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ API响应转换测试失败: {e}")
            return False
    
    async def test_convenience_functions(self) -> bool:
        """测试便捷函数"""
        logger.info("🔄 测试便捷函数...")
        
        try:
            # 测试便捷新闻转换函数
            raw_news = {
                "title": "便捷函数测试新闻",
                "description": "测试便捷转换函数的功能",
                "link": "https://test.com/news"
            }
            
            converted_news = convert_news_data(raw_news, "rss", "测试源")
            assert isinstance(converted_news, StandardNewsArticle)
            assert converted_news.title == "便捷函数测试新闻"
            
            logger.info(f"  ✅ 便捷新闻转换: {converted_news.title}")
            
            # 测试JSON转换
            json_str = convert_to_json(converted_news, indent=2)
            assert isinstance(json_str, str)
            assert "便捷函数测试新闻" in json_str
            
            logger.info(f"  ✅ JSON转换: {len(json_str)} 字符")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ 便捷函数测试失败: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """运行所有测试"""
        logger.info("🚀 开始 data_converter 完整测试...")
        
        results = {
            "news_conversion": await self.test_news_conversion(),
            "analysis_conversion": await self.test_analysis_conversion(), 
            "api_response_conversion": await self.test_api_response_conversion(),
            "convenience_functions": await self.test_convenience_functions()
        }
        
        # 统计结果
        passed = sum(results.values())
        total = len(results)
        
        logger.info("📊 测试结果汇总:")
        for test_name, result in results.items():
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"  {test_name}: {status}")
        
        logger.info(f"📈 总体结果: {passed}/{total} 测试通过")
        
        if passed == total:
            logger.info("🎉 data_converter 模块所有测试通过！")
        else:
            logger.warning(f"⚠️ 有 {total - passed} 个测试失败，需要修复")
        
        return results

async def main():
    """主测试函数"""
    tester = TestDataConverter()
    results = await tester.run_all_tests()
    
    # 返回成功状态
    return all(results.values())

if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())
    
    if success:
        print("\n✅ data_converter 模块验证完成 - 所有功能正常")
        exit(0)
    else:
        print("\n❌ data_converter 模块验证失败 - 存在问题需要修复") 
        exit(1) 