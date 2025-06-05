#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AI代理数据转换器测试

用于测试AI分析模块中的数据转换功能，包括：
1. 新闻数据转换器测试
2. 分析结果转换器测试  
3. API响应转换器测试
4. 数据库模型转换器测试
"""

import pytest
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path
import sys

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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

@pytest.fixture
def news_converter():
    """新闻数据转换器fixture"""
    return NewsDataConverter()

@pytest.fixture
def analysis_converter():
    """分析结果转换器fixture"""
    return AnalysisResultConverter()

@pytest.fixture
def api_converter():
    """API响应转换器fixture"""
    return APIResponseConverter()

@pytest.fixture
def db_converter():
    """数据库模型转换器fixture"""
    return DatabaseModelConverter()

@pytest.mark.unit
class TestDataConverter:
    """数据转换器测试类"""
    
    def test_news_conversion(self, news_converter):
        """测试新闻数据转换"""
        logger.info("🔄 测试新闻数据转换...")
        
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
        
        article = news_converter.convert_to_standard(
            rss_data, "rss", "财经网", 1
        )
        
        # 验证转换结果
        assert article.title == "某科技公司发布新产品，股价上涨8%"
        assert article.source_name == "财经网"
        assert article.source_id == 1
        assert article.author == "财经记者李明"
        assert article.category == "科技股"
        assert isinstance(article.tags, list)
        
        logger.info(f"  ✅ RSS转换成功: {article.title}")
        
        # 测试雪球数据转换
        xueqiu_data = {
            "title": "热门股票分析：AI概念股持续走强",
            "text": "多只AI概念股今日表现强劲，板块整体上涨超过5%。机构资金持续流入，看好后市发展。",
            "target": "https://xueqiu.com/status/123456",
            "created_at": 1737974400,  # Unix时间戳
            "user": "雪球分析师"
        }
        
        xq_article = news_converter.convert_to_standard(
            xueqiu_data, "xueqiu", "雪球", 2
        )
        
        assert xq_article.title == "热门股票分析：AI概念股持续走强"
        assert xq_article.source_name == "雪球"
        assert xq_article.author == "雪球分析师"
        
        logger.info(f"  ✅ 雪球转换成功: {xq_article.title}")
        
        # 测试批量转换
        batch_data = [rss_data, xueqiu_data]
        batch_results = news_converter.convert_batch(
            batch_data, "rss", "综合财经", 3
        )
        
        assert len(batch_results) == 2
        logger.info(f"  ✅ 批量转换成功: {len(batch_results)} 篇文章")
    
    def test_analysis_conversion(self, analysis_converter):
        """测试分析结果转换"""
        logger.info("🔄 测试分析结果转换...")
        
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
        sentiment_converted = analysis_converter.convert_sentiment_result(sentiment_result)
        assert sentiment_converted["sentiment_score"] == 7.8
        assert sentiment_converted["sentiment_label"] == "积极"
        assert sentiment_converted["confidence"] == 0.88
        
        logger.info(f"  ✅ 情感分析转换: 评分{sentiment_converted['sentiment_score']}, 标签{sentiment_converted['sentiment_label']}")
        
        # 转换投资分析结果
        investment_converted = analysis_converter.convert_investment_result(investment_result)
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
        
        complete_result = analysis_converter.convert_complete_analysis(
            mock_article, sentiment_result, investment_result, 2.5
        )
        
        assert complete_result.article_id == 1
        assert complete_result.sentiment_score == 7.8
        assert complete_result.processing_time == 2.5
        assert len(complete_result.recommendations) > 0
        
        logger.info(f"  ✅ 完整分析转换: 文章ID{complete_result.article_id}, 处理时间{complete_result.processing_time}秒")
    
    def test_api_response_conversion(self, api_converter):
        """测试API响应转换"""
        logger.info("🔄 测试API响应转换...")
        
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
        api_response = api_converter.convert_analysis_response(analysis_result)
        assert api_response["status"] == "success"
        assert api_response["data"]["article_id"] == 123
        assert "sentiment" in api_response["data"]
        assert "investment" in api_response["data"]
        
        logger.info(f"  ✅ 单个结果转换: 状态{api_response['status']}, 文章ID{api_response['data']['article_id']}")
        
        # 转换批量结果
        batch_results = [analysis_result, analysis_result]  # 模拟多个结果
        batch_response = api_converter.convert_batch_analysis_response(batch_results, 6.4)
        
        assert batch_response["status"] == "success"
        assert len(batch_response["data"]["results"]) == 2
        assert batch_response["data"]["metadata"]["total_articles"] == 2
        
        logger.info(f"  ✅ 批量结果转换: 总数{batch_response['data']['metadata']['total_articles']}, 结果数{len(batch_response['data']['results'])}")
    
    def test_database_conversion(self, db_converter):
        """测试数据库模型转换"""
        logger.info("🔄 测试数据库模型转换...")
        
        # 创建标准分析结果
        analysis_result = StandardAnalysisResult(
            article_id=456,
            sentiment_score=8.2,
            sentiment_label="非常积极",
            confidence=0.92,
            key_phrases=["重大突破", "业绩飙升", "市场领先"],
            investment_opportunities=[
                {
                    "type": "技术突破",
                    "industry": "人工智能",
                    "score": 9.1,
                    "confidence": 0.89
                }
            ],
            risk_factors=["估值过高", "技术风险"],
            recommendations=[
                {
                    "action": "强烈买入",
                    "position": "重仓配置 (30-40%)",
                    "timeframe": "长期持有",
                    "rationale": "技术突破带来长期增长动力"
                }
            ],
            analysis_timestamp=datetime.now(timezone.utc),
            processing_time=4.8
        )
        
        # 测试转换为字典
        result_dict = db_converter.convert_to_dict(analysis_result)
        assert isinstance(result_dict, dict)
        assert result_dict["article_id"] == 456
        assert result_dict["sentiment_score"] == 8.2
        
        logger.info(f"  ✅ 对象转字典: 文章ID{result_dict['article_id']}, 评分{result_dict['sentiment_score']}")
        
        # 测试从字典转换
        reconstructed = db_converter.convert_from_dict(result_dict, StandardAnalysisResult)
        assert isinstance(reconstructed, StandardAnalysisResult)
        assert reconstructed.article_id == 456
        assert reconstructed.sentiment_score == 8.2
        
        logger.info(f"  ✅ 字典转对象: 文章ID{reconstructed.article_id}, 评分{reconstructed.sentiment_score}")
    
    def test_convenience_functions(self):
        """测试便捷功能函数"""
        logger.info("🔄 测试便捷功能函数...")
        
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
    
    def run_all_tests(self, news_converter, analysis_converter, api_converter, db_converter):
        """运行所有测试"""
        logger.info("🚀 开始运行数据转换器完整测试套件...")
        
        results = {}
        
        # 依次运行各项测试
        try:
            self.test_news_conversion(news_converter)
            results["news_conversion"] = True
        except Exception as e:
            logger.error(f"新闻转换测试失败: {e}")
            results["news_conversion"] = False
        
        try:
            self.test_analysis_conversion(analysis_converter)
            results["analysis_conversion"] = True
        except Exception as e:
            logger.error(f"分析转换测试失败: {e}")
            results["analysis_conversion"] = False
        
        try:
            self.test_api_response_conversion(api_converter)
            results["api_response_conversion"] = True
        except Exception as e:
            logger.error(f"API响应转换测试失败: {e}")
            results["api_response_conversion"] = False
        
        try:
            self.test_database_conversion(db_converter)
            results["database_conversion"] = True
        except Exception as e:
            logger.error(f"数据库转换测试失败: {e}")
            results["database_conversion"] = False
        
        try:
            self.test_convenience_functions()
            results["convenience_functions"] = True
        except Exception as e:
            logger.error(f"便捷功能测试失败: {e}")
            results["convenience_functions"] = False
        
        # 输出测试结果
        logger.info("\n📊 测试结果汇总:")
        success_count = 0
        for test_name, success in results.items():
            status = "✅ 通过" if success else "❌ 失败"
            logger.info(f"  {test_name}: {status}")
            if success:
                success_count += 1
        
        total_tests = len(results)
        logger.info(f"\n🎯 总体结果: {success_count}/{total_tests} 通过")
        
        return results


def main():
    """独立运行测试的主函数"""
    test_suite = TestDataConverter()
    
    # 创建转换器实例
    news_conv = NewsDataConverter()
    analysis_conv = AnalysisResultConverter()
    api_conv = APIResponseConverter()
    db_conv = DatabaseModelConverter()
    
    results = test_suite.run_all_tests(news_conv, analysis_conv, api_conv, db_conv)
    
    # 根据测试结果设置退出码
    all_passed = all(results.values())
    if all_passed:
        logger.info("🎉 所有测试通过！")
        return 0
    else:
        logger.error("💥 部分测试失败！")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code) 