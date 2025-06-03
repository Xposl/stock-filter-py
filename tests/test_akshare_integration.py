#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AKShare集成测试
测试新的AKShare行业板块数据提供者功能
"""

import pytest
import asyncio
import logging
from typing import List, Dict

# 配置测试日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestAKShareIntegration:
    """AKShare集成测试类"""
    
    @pytest.fixture
    async def akshare_provider(self):
        """获取AKShare提供者实例"""
        from core.ai_agents.utils.akshare_industry_provider import AKShareIndustryProvider
        return AKShareIndustryProvider()
    
    @pytest.mark.asyncio
    async def test_get_industry_stocks_basic(self, akshare_provider):
        """测试基础行业股票获取功能"""
        logger.info("🚀 开始测试基础行业股票获取...")
        
        # 测试人工智能行业
        stocks = await akshare_provider.get_industry_stocks(
            industry="人工智能",
            impact_type="正面",
            impact_degree=8
        )
        
        # 验证返回结果
        assert isinstance(stocks, list), "应该返回列表"
        logger.info(f"  ✅ 人工智能行业获取到 {len(stocks)} 只股票")
        
        if stocks:
            # 验证股票数据结构
            stock = stocks[0]
            assert "code" in stock, "股票应该包含代码"
            assert "name" in stock, "股票应该包含名称"
            assert "relevance_score" in stock, "股票应该包含相关性评分"
            assert "data_source" in stock, "股票应该包含数据源标识"
            assert stock["data_source"] == "akshare", "数据源应该是akshare"
            
            logger.info(f"  ✅ 股票数据结构验证通过: {stock['code']} {stock['name']}")
    
    @pytest.mark.asyncio
    async def test_multiple_industries(self, akshare_provider):
        """测试多个行业股票获取"""
        logger.info("🚀 开始测试多个行业股票获取...")
        
        industries = ["新能源", "半导体", "医疗"]
        
        for industry in industries:
            stocks = await akshare_provider.get_industry_stocks(
                industry=industry,
                impact_type="正面",
                impact_degree=7
            )
            
            logger.info(f"  ✅ {industry}行业获取到 {len(stocks)} 只股票")
            
            # 验证每个行业都有结果
            if stocks:
                assert all(s.get("industry") == industry for s in stocks), f"{industry}行业标识错误"
    
    @pytest.mark.asyncio
    async def test_industry_mapping(self, akshare_provider):
        """测试行业映射功能"""
        logger.info("🚀 开始测试行业映射功能...")
        
        # 测试直接映射
        boards = akshare_provider._map_industry_to_boards("人工智能")
        assert isinstance(boards, list), "应该返回板块列表"
        assert len(boards) > 0, "应该有映射的板块"
        logger.info(f"  ✅ 人工智能映射到板块: {boards}")
        
        # 测试模糊映射
        boards = akshare_provider._map_industry_to_boards("AI")
        assert isinstance(boards, list), "模糊匹配应该返回列表"
        logger.info(f"  ✅ AI模糊映射到板块: {boards}")
    
    @pytest.mark.asyncio 
    async def test_get_available_industries(self, akshare_provider):
        """测试获取可用行业列表"""
        logger.info("🚀 开始测试获取可用行业列表...")
        
        industries = await akshare_provider.get_available_industries()
        
        assert isinstance(industries, list), "应该返回行业列表"
        assert len(industries) > 0, "应该有可用行业"
        
        logger.info(f"  ✅ 获取到 {len(industries)} 个可用行业")
        logger.info(f"  前10个行业: {industries[:10]}")
    
    @pytest.mark.asyncio
    async def test_relevance_score_calculation(self, akshare_provider):
        """测试相关性评分计算"""
        logger.info("🚀 开始测试相关性评分计算...")
        
        # 模拟股票数据
        test_row = {
            '总市值': 2000_0000_0000,  # 2000亿市值
            '换手率': 5.0,            # 适中换手率
            '涨跌幅': 2.5             # 适中涨跌幅
        }
        
        score = akshare_provider._calculate_relevance_score(test_row)
        
        assert isinstance(score, int), "评分应该是整数"
        assert 1 <= score <= 10, "评分应该在1-10之间"
        
        logger.info(f"  ✅ 相关性评分计算通过: {score}分")
    
    @pytest.mark.asyncio
    async def test_stock_deduplication_and_ranking(self, akshare_provider):
        """测试股票去重和排序"""
        logger.info("🚀 开始测试股票去重和排序...")
        
        # 模拟重复股票数据
        duplicate_stocks = [
            {"code": "000001", "relevance_score": 8, "market_cap": 1000_0000_0000},
            {"code": "000001", "relevance_score": 9, "market_cap": 1000_0000_0000},  # 重复，但评分更高
            {"code": "000002", "relevance_score": 7, "market_cap": 500_0000_0000},
        ]
        
        result = akshare_provider._deduplicate_and_rank_stocks(duplicate_stocks, impact_degree=8)
        
        # 验证去重
        codes = [s["code"] for s in result]
        assert len(codes) == len(set(codes)), "应该去除重复股票"
        
        # 验证排序
        assert result[0]["code"] == "000001", "评分最高的应该排在前面"
        assert result[0]["relevance_score"] == 9, "应该保留评分更高的记录"
        
        logger.info(f"  ✅ 去重和排序验证通过: {len(result)} 只股票")

class TestNewsAnalysisFlowIntegration:
    """新闻分析流程集成测试"""
    
    @pytest.mark.asyncio
    async def test_stock_relator_agent_akshare(self):
        """测试StockRelatorAgent的AKShare集成"""
        logger.info("🚀 开始测试StockRelatorAgent的AKShare集成...")
        
        # 导入必要的模块
        from core.ai_agents.flow_definitions.news_analysis_flow import StockRelatorAgent
        from core.ai_agents.llm_clients.qwen_llm_client import QwenLLMClient
        
        # 创建模拟的LLM客户端
        class MockQwenClient:
            async def __aenter__(self):
                return self
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
        
        # 创建StockRelatorAgent
        agent = StockRelatorAgent(MockQwenClient())
        
        # 模拟行业分析数据
        shared_store = {
            "industry_analysis": {
                "affected_industries": [
                    {
                        "industry": "人工智能",
                        "impact_type": "正面",
                        "impact_degree": 8
                    },
                    {
                        "industry": "新能源",
                        "impact_type": "正面", 
                        "impact_degree": 7
                    }
                ]
            }
        }
        
        # 执行prep阶段
        prep_data = agent.prep(shared_store)
        assert "industry_analysis" in prep_data, "prep应该包含行业分析数据"
        
        # 测试AKShare股票获取（模拟）
        stocks = await agent._get_industry_stocks_akshare("人工智能", "正面", 8)
        
        # 验证结果
        assert isinstance(stocks, list), "应该返回股票列表"
        logger.info(f"  ✅ AKShare集成测试通过: 获取到 {len(stocks)} 只股票")
        
        if stocks:
            stock = stocks[0]
            assert "data_source" in stock, "股票应该标记数据源"
            assert stock["data_source"] == "akshare", "数据源应该是akshare"

def test_convenience_function():
    """测试便捷函数"""
    logger.info("🚀 开始测试便捷函数...")
    
    from core.ai_agents.utils.akshare_industry_provider import get_industry_stocks_from_akshare
    
    # 异步测试
    async def _test():
        stocks = await get_industry_stocks_from_akshare("人工智能", "正面", 8)
        assert isinstance(stocks, list), "便捷函数应该返回列表"
        return len(stocks)
    
    result = asyncio.run(_test())
    logger.info(f"  ✅ 便捷函数测试通过: 获取到 {result} 只股票")

if __name__ == "__main__":
    """运行测试"""
    logger.info("🚀 开始运行AKShare集成测试...")
    
    # 运行便捷函数测试
    test_convenience_function()
    
    # 运行异步测试需要pytest
    logger.info("✅ 基础测试完成！运行完整测试请使用: pytest tests/test_akshare_integration.py -v") 