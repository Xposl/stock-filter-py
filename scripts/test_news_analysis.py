#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试增强版新闻分析系统修复效果
验证问题1-4的修复情况：
1. NewsArticle模型适配真实数据库
2. 股票检测逻辑修复  
3. AKShare行业股票筛选修复
4. 性能优化（0只股票时跳过LLM）
"""

import asyncio
import logging
import sys
import os
import json
from datetime import datetime
from typing import List, Dict, Any

from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from core.models.news_article import NewsArticle
from core.ai_agents.llm_clients.qwen_client import QwenLLMClient
from core.ai_agents.flow_definitions.news_analysis_flow import NewsAnalysisFlow

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 测试用例 - 包含之前导致问题的新闻
TEST_CASES = [
    {
        "name": "测试案例1: 香港股票检测",
        "title": "沪上阿姨(02589)：悉数行使超额配股权、稳定价格行动及稳定价格期结束", 
        "content": None,
        "expected_type": "stock_specific",
        "expected_stocks": ["02589"],
        "test_problems": [1, 2]  # 测试问题2：股票检测逻辑
    }
    # {
    #     "name": "测试案例1: 香港股票检测",
    #     "title": "友谊时光(06820)股价异动", 
    #     "content": "友谊时光(06820)今日股价大涨，市场关注度较高。该公司主要从事餐饮业务。",
    #     "expected_type": "stock_specific",
    #     "expected_stocks": ["06820"],
    #     "test_problems": [2]  # 测试问题2：股票检测逻辑
    # },
    # {
    #     "name": "测试案例2: A股股票检测",
    #     "title": "平安银行(000001)发布业绩预告",
    #     "content": "平安银行(000001)发布2024年业绩预告，预计净利润同比增长5%-10%。",
    #     "expected_type": "stock_specific", 
    #     "expected_stocks": ["000001"],
    #     "test_problems": [2]
    # },
    # {
    #     "name": "测试案例3: 行业新闻（新能源）",
    #     "title": "新能源汽车行业政策利好",
    #     "content": "国家发改委发布新能源汽车产业发展规划，明确2025年新能源汽车销量目标。涉及动力电池、充电桩等多个细分领域。",
    #     "expected_type": "industry_focused",
    #     "expected_industries": ["新能源汽车", "新能源"],
    #     "test_problems": [3, 4]  # 测试问题3和4：AKShare筛选和性能优化
    # },
    # {
    #     "name": "测试案例4: 行业新闻（医药）",
    #     "title": "医药行业监管新规出台",
    #     "content": "国家药监局发布医药行业新规，对生物制药、医疗器械等领域提出新要求。",
    #     "expected_type": "industry_focused",
    #     "expected_industries": ["医药", "生物医药"],
    #     "test_problems": [3, 4]
    # },
    # {
    #     "name": "测试案例5: 空内容测试（测试问题1）",
    #     "title": "外部新闻链接标题",
    #     "content": None,  # 模拟数据库中content为NULL的情况
    #     "url": "https://example.com/news/123",
    #     "test_problems": [1],  # 测试问题1：动态内容获取
    #     "expected_type": "unknown"
    # }
]

class NewsAnalysisFixTester:
    """新闻分析修复验证测试器"""
    
    def __init__(self):
        """初始化测试器"""
        # 🔧 启用测试模式，避免数据库连接问题
        self.test_mode = True
        logger.info("🧪 启动测试模式，避免数据库连接问题")
        
        # 初始化千问客户端
        self.llm_client = QwenLLMClient()
        
        # 🔧 使用测试模式初始化分析流程，避免数据库连接
        self.analysis_flow = NewsAnalysisFlow(self.llm_client, test_mode=self.test_mode)
        self.test_results = []
    
    async def run_all_tests(self):
        """运行所有测试用例"""
        logger.info("🚀 开始新闻分析修复效果测试")
        logger.info(f"📋 测试用例总数: {len(TEST_CASES)}")
        
        for i, test_case in enumerate(TEST_CASES, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"🧪 测试 {i}/{len(TEST_CASES)}: {test_case['name']}")
            logger.info(f"🎯 测试问题: {test_case.get('test_problems', [])}")
            
            try:
                result = await self.test_single_case(test_case)
                self.test_results.append(result)
                
                # 显示测试结果
                self.print_test_result(result)
                
            except Exception as e:
                logger.error(f"❌ 测试失败: {e}")
                self.test_results.append({
                    "test_name": test_case['name'],
                    "success": False,
                    "error": str(e)
                })
        
        # 生成测试报告
        await self.generate_test_report()
    
    async def test_single_case(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """测试单个用例"""
        
        # 🔥 测试问题1: 创建真实的NewsArticle对象（可能content为空）
        test_id = int(datetime.now().timestamp() * 1000)  # 转换为整数毫秒时间戳
        test_url = test_case.get("url", "https://example.com")
        url_hash = f"hash_{test_id}"  # 生成简单的hash
        
        article = NewsArticle(
            id=test_id,
            title=test_case["title"],
            content=test_case.get("content"),  # 可能为None
            url=test_url,
            url_hash=url_hash,
            source_id=1,
            created_at=datetime.now()
        )
        
        start_time = datetime.now()
        
        # 执行分析
        analysis_result = await self.analysis_flow.analyze_news_with_article_async(article)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 分析测试结果
        test_result = {
            "test_name": test_case["name"],
            "test_problems": test_case.get("test_problems", []),
            "processing_time": processing_time,
            "success": True,
            "issues_found": [],
            "fixes_verified": [],
            "analysis_details": {
                "analysis_type": analysis_result.analysis_type,
                "mentioned_stocks_count": len(analysis_result.mentioned_stocks),
                "related_stocks_count": len(analysis_result.related_stocks),
                "mentioned_stocks": analysis_result.mentioned_stocks,
                "related_stocks": analysis_result.related_stocks[:3],  # 只显示前3个
                "investment_advice": analysis_result.investment_advice
            }
        }
        
        # 验证修复效果
        await self.verify_fixes(test_case, analysis_result, test_result)
        
        return test_result
    
    async def verify_fixes(self, test_case: Dict, analysis_result, test_result: Dict):
        """验证各个问题的修复效果"""
        test_problems = test_case.get("test_problems", [])
        
        for problem_id in test_problems:
            if problem_id == 1:
                # 🔥 验证问题1: NewsArticle模型适配
                await self.verify_problem_1(test_case, analysis_result, test_result)
            elif problem_id == 2:
                # 🔥 验证问题2: 股票检测逻辑
                await self.verify_problem_2(test_case, analysis_result, test_result)
            elif problem_id == 3:
                # 🔥 验证问题3: AKShare行业股票筛选
                await self.verify_problem_3(test_case, analysis_result, test_result)
            elif problem_id == 4:
                # 🔥 验证问题4: 性能优化
                await self.verify_problem_4(test_case, analysis_result, test_result)
    
    async def verify_problem_1(self, test_case: Dict, analysis_result, test_result: Dict):
        """验证问题1: NewsArticle模型适配真实数据库"""
        if test_case.get("content") is None:
            # 验证是否正确处理了空content的情况
            if hasattr(analysis_result.article, 'get_analysis_content'):
                content = analysis_result.article.get_analysis_content()
                if content and len(content) > 0:
                    test_result["fixes_verified"].append("问题1: ✅ 成功获取动态内容")
                else:
                    test_result["issues_found"].append("问题1: ❌ 未能获取动态内容")
            else:
                test_result["issues_found"].append("问题1: ❌ 缺少get_analysis_content方法")
        else:
            test_result["fixes_verified"].append("问题1: ✅ 有内容的情况正常处理")
    
    async def verify_problem_2(self, test_case: Dict, analysis_result, test_result: Dict):
        """验证问题2: 股票检测逻辑修复"""
        expected_type = test_case.get("expected_type")
        expected_stocks = test_case.get("expected_stocks", [])
        
        # 检查分析类型是否正确
        if analysis_result.analysis_type == expected_type:
            test_result["fixes_verified"].append(f"问题2: ✅ 分析类型正确 ({expected_type})")
        else:
            test_result["issues_found"].append(
                f"问题2: ❌ 分析类型错误，期望: {expected_type}, 实际: {analysis_result.analysis_type}"
            )
        
        # 检查是否正确识别了股票
        mentioned_codes = [stock.get("code", "") for stock in analysis_result.mentioned_stocks]
        for expected_code in expected_stocks:
            if any(expected_code in code for code in mentioned_codes):
                test_result["fixes_verified"].append(f"问题2: ✅ 正确识别股票 {expected_code}")
            else:
                test_result["issues_found"].append(f"问题2: ❌ 未识别股票 {expected_code}")
    
    async def verify_problem_3(self, test_case: Dict, analysis_result, test_result: Dict):
        """验证问题3: AKShare行业股票筛选修复"""
        related_stocks_count = len(analysis_result.related_stocks)
        
        if related_stocks_count > 0:
            test_result["fixes_verified"].append(f"问题3: ✅ AKShare成功获取 {related_stocks_count} 只相关股票")
            
            # 检查是否包含AKShare数据源标识
            akshare_stocks = [
                stock for stock in analysis_result.related_stocks 
                if "akshare" in stock.get("analysis_source", "").lower()
            ]
            if akshare_stocks:
                test_result["fixes_verified"].append(f"问题3: ✅ 含有 {len(akshare_stocks)} 只AKShare来源股票")
            else:
                test_result["issues_found"].append("问题3: ❌ 未发现AKShare来源的股票")
        else:
            test_result["issues_found"].append("问题3: ❌ AKShare未返回任何股票（可能仍有问题）")
    
    async def verify_problem_4(self, test_case: Dict, analysis_result, test_result: Dict):
        """验证问题4: 性能优化（0只股票时跳过LLM）"""
        related_stocks_count = len(analysis_result.related_stocks)
        mentioned_stocks_count = len(analysis_result.mentioned_stocks)
        
        investment_advice = analysis_result.investment_advice
        token_saved = investment_advice.get("token_saved", False)
        
        if related_stocks_count == 0 and mentioned_stocks_count == 0:
            if token_saved:
                test_result["fixes_verified"].append("问题4: ✅ 0只股票时成功跳过LLM分析，节省token")
            else:
                test_result["issues_found"].append("问题4: ❌ 0只股票时仍然调用了LLM")
        else:
            if not token_saved:
                test_result["fixes_verified"].append("问题4: ✅ 有股票数据时正常使用LLM分析")
            else:
                test_result["issues_found"].append("问题4: ❌ 有股票数据时错误跳过了LLM")
    
    def print_test_result(self, result: Dict):
        """打印测试结果"""
        print(f"\n📊 测试结果: {result['test_name']}")
        print(f"⏱️  处理时间: {result['processing_time']:.2f}秒")
        
        if result["fixes_verified"]:
            print("✅ 修复验证通过:")
            for fix in result["fixes_verified"]:
                print(f"   {fix}")
        
        if result["issues_found"]:
            print("❌ 发现问题:")
            for issue in result["issues_found"]:
                print(f"   {issue}")
        
        details = result["analysis_details"]
        print(f"📈 分析详情:")
        print(f"   - 分析类型: {details['analysis_type']}")
        print(f"   - 提及股票: {details['mentioned_stocks_count']}只")
        print(f"   - 相关股票: {details['related_stocks_count']}只")
        
        if details["mentioned_stocks"]:
            stocks_info = [f"{s['code']}({s.get('name', '')})" for s in details['mentioned_stocks']]
            print(f"   - 提及的股票: {stocks_info}")
        
        if details["related_stocks"]:
            stocks_info = [f"{s['code']}({s.get('name', '')})-{s.get('current_score', 0)}分" for s in details['related_stocks']]
            print(f"   - 相关股票(前3): {stocks_info}")
        
        advice = details["investment_advice"]
        print(f"   - 投资建议: {advice.get('recommendation', 'N/A')}")
        if advice.get("token_saved"):
            print(f"   - Token节省: ✅ (跳过LLM分析)")
        else:
            print(f"   - LLM分析: ✅ (正常调用)")
    
    async def generate_test_report(self):
        """生成测试报告"""
        logger.info(f"\n{'='*80}")
        logger.info("📝 测试报告汇总")
        logger.info(f"{'='*80}")
        
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r["success"])
        total_fixes = sum(len(r.get("fixes_verified", [])) for r in self.test_results)
        total_issues = sum(len(r.get("issues_found", [])) for r in self.test_results)
        
        logger.info(f"📊 测试统计:")
        logger.info(f"   - 总测试数: {total_tests}")
        logger.info(f"   - 成功测试: {successful_tests}")
        logger.info(f"   - 修复验证: {total_fixes}项")
        logger.info(f"   - 发现问题: {total_issues}项")
        
        # 按问题分类统计
        problem_stats = {1: {"fixed": 0, "issues": 0}, 2: {"fixed": 0, "issues": 0}, 
                        3: {"fixed": 0, "issues": 0}, 4: {"fixed": 0, "issues": 0}}
        
        for result in self.test_results:
            for fix in result.get("fixes_verified", []):
                for p in range(1, 5):
                    if f"问题{p}" in fix:
                        problem_stats[p]["fixed"] += 1
            
            for issue in result.get("issues_found", []):
                for p in range(1, 5):
                    if f"问题{p}" in issue:
                        problem_stats[p]["issues"] += 1
        
        logger.info(f"\n📋 问题修复统计:")
        problem_names = {
            1: "NewsArticle模型适配",
            2: "股票检测逻辑修复", 
            3: "AKShare行业筛选",
            4: "性能优化"
        }
        
        for p in range(1, 5):
            fixed = problem_stats[p]["fixed"]
            issues = problem_stats[p]["issues"]
            status = "✅ 修复成功" if fixed > issues else "❌ 仍有问题" if issues > 0 else "⚪ 未测试"
            logger.info(f"   问题{p} ({problem_names[p]}): {status} (验证{fixed}项, 问题{issues}项)")
        
        # 保存详细报告
        report_file = f"test_fix_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"\n📄 详细报告已保存: {report_file}")

async def main():
    """主测试函数"""
    tester = NewsAnalysisFixTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 