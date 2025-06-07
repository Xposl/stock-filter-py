#!/usr/bin/env python3

"""
新闻分析流程测试脚本

基于 core/ai_agents/news_analysis_flow/flows.py 中定义的 PocketFlow 流程，
测试完整的新闻分析功能，验证各个节点的工作状态和数据流转。

主要功能:
    - 测试股票特定新闻的分析流程
    - 测试行业导向新闻的分析流程
    - 验证节点间的数据传递和状态转换
    - 提供详细的执行日志和结果展示

使用方法:
    python scripts/test_news_analysis_flow.py
"""

import logging
import os
import sys
import traceback
from datetime import datetime
from typing import Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 导入必要的模块
from core.ai_agents.news_analysis_flow.flows import news_analysis_flow  # noqa: E402
from core.models.news_article import NewsArticle  # noqa: E402

# 创建logs目录（如果不存在）
logs_dir = os.path.join(project_root, 'logs')
os.makedirs(logs_dir, exist_ok=True)

# 生成带时间戳的日志文件名
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_filename = f'test_news_analysis_flow_{timestamp}.log'
log_filepath = os.path.join(logs_dir, log_filename)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_filepath, mode='w', encoding='utf-8')
    ],
    force=True  # 强制重新配置日志
)
logger = logging.getLogger(__name__)

# 记录日志文件位置
logger.info(f"📄 日志文件位置: {log_filepath}")

class NewsAnalysisFlowTester:
    """新闻分析流程测试器"""

    def __init__(self):
        """初始化测试器"""
        self.test_results = []
        self.flow = None
        self.log_filepath = log_filepath

    def setup_flow(self):
        """设置新闻分析流程"""
        try:
            logger.info("🚀 初始化新闻分析流程...")
            self.flow = news_analysis_flow()
            logger.info(f"✅ 流程初始化成功，起始节点: {self.flow.start_node.__class__.__name__}")
            return True
        except Exception as e:
            logger.error(f"❌ 流程初始化失败: {e}")
            logger.error(traceback.format_exc())
            return False

    def create_test_articles(self) -> list[NewsArticle]:
        """创建测试新闻文章"""
        test_articles = [
            # 股票特定新闻
            NewsArticle(
                id=1,
                title="沪上阿姨(02589)：悉数行使超额配股权、稳定价格行动及稳定价格期结束",
                content="沪上阿姨公司发布公告，宣布悉数行使超额配股权，稳定价格行动正式结束。公司表示将继续专注茶饮业务发展，为股东创造更大价值。",
                url="https://example.com/news1",
                url_hash="hash1",
                source_id=1,
                created_at=datetime.now()
            )
            # 另一个股票特定新闻
            # NewsArticle(
            #     id=2,
            #     title="平安银行(000001.SZ)发布2024年第三季度业绩报告",
            #     content="平安银行发布2024年第三季度财报，净利润同比增长8.5%，零售业务持续增长，资产质量保持稳定。",
            #     url="https://example.com/news2",
            #     url_hash="hash2",
            #     source_id=1,
            #     created_at=datetime.now()
            # ),
            # # 行业导向新闻
            # NewsArticle(
            #     id=3,
            #     title="人工智能行业发展迎来新机遇，多家公司加码AI技术投入",
            #     content="随着ChatGPT等大模型的快速发展，人工智能行业迎来新一轮发展热潮。多家科技公司纷纷加大AI技术研发投入，抢占市场先机。",
            #     url="https://example.com/news3",
            #     url_hash="hash3",
            #     source_id=1,
            #     created_at=datetime.now()
            # ),
            # # 另一个行业导向新闻
            # NewsArticle(
            #     id=4,
            #     title="新能源汽车市场持续火热，政策利好推动产业发展",
            #     content="在政策利好和技术进步双重推动下，新能源汽车市场持续火热。电池技术、充电基础设施、智能驾驶等领域都迎来快速发展。",
            #     url="https://example.com/news4",
            #     url_hash="hash4",
            #     source_id=1,
            #     created_at=datetime.now()
            # ),
            # # 医药行业新闻
            # NewsArticle(
            #     id=5,
            #     title="生物医药行业迎来创新药研发热潮，多个新药获批上市",
            #     content="近期多个创新药获得药监局批准上市，生物医药行业创新活力持续释放。免疫治疗、精准医疗等领域成为投资热点。",
            #     url="https://example.com/news5",
            #     url_hash="hash5",
            #     source_id=1,
            #     created_at=datetime.now()
            # )
        ]

        logger.info(f"📄 创建了 {len(test_articles)} 篇测试新闻文章")
        return test_articles

    def test_single_article(self, article: NewsArticle, test_name: str) -> dict[str, Any]:
        """测试单篇文章的分析流程"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🔍 开始测试: {test_name}")
        logger.info(f"📰 文章标题: {article.title}")
        logger.info(f"{'='*80}")

        test_result = {
            'test_name': test_name,
            'article_title': article.title,
            'success': False,
            'execution_time': 0,
            'error': None,
            'shared_store': None,
            'analysis_type': None,
            'mentioned_stocks': [],
            'mentioned_industries': []
        }

        try:
            start_time = datetime.now()

            # 准备共享存储
            shared_store = {
                'article': article,
                'title': '',
                'content': '',
                'mentioned_stocks': [],
                'mentioned_industries': []
            }

            logger.info("🚀 开始执行新闻分析流程...")

            # 执行流程
            result = self.flow.run(shared_store)

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            # 记录结果
            test_result.update({
                'success': True,
                'execution_time': execution_time,
                'shared_store': shared_store.copy(),
                'analysis_type': self._get_analysis_type_from_store(shared_store),
                'mentioned_stocks': shared_store.get('mentioned_stocks', []),
                'mentioned_industries': shared_store.get('mentioned_industries', [])
            })

            # 输出详细结果
            self._print_test_results(test_result)

            logger.info(f"✅ 测试 '{test_name}' 执行成功！耗时: {execution_time:.2f}秒")

        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds() if 'start_time' in locals() else 0

            test_result.update({
                'success': False,
                'execution_time': execution_time,
                'error': str(e)
            })

            logger.error(f"❌ 测试 '{test_name}' 执行失败: {e}")
            logger.error(f"错误详情: {traceback.format_exc()}")

        return test_result

    def _get_analysis_type_from_store(self, shared_store: dict[str, Any]) -> str:
        """从共享存储中推断分析类型"""
        stocks = shared_store.get('mentioned_stocks', [])
        industries = shared_store.get('mentioned_industries', [])

        if stocks and len(stocks) > 0:
            return 'stock_specific'
        elif industries and len(industries) > 0:
            return 'industry_focused'
        else:
            return 'unknown'

    def _print_test_results(self, test_result: dict[str, Any]):
        """打印测试结果"""
        logger.info("\n📊 测试结果详情:")
        logger.info(f"   🎯 分析类型: {test_result.get('analysis_type', 'unknown')}")
        logger.info(f"   📈 提及股票: {len(test_result.get('mentioned_stocks', []))} 只")

        for i, stock in enumerate(test_result.get('mentioned_stocks', []), 1):
            if isinstance(stock, dict):
                name = stock.get('name', '未知')
                code = stock.get('code', '未知')
                logger.info(f"      {i}. {name} ({code})")
            else:
                logger.info(f"      {i}. {stock}")

        logger.info(f"   🏭 提及行业: {len(test_result.get('mentioned_industries', []))} 个")
        for i, industry in enumerate(test_result.get('mentioned_industries', []), 1):
            logger.info(f"      {i}. {industry}")

        shared_store = test_result.get('shared_store', {})
        logger.info(f"   📝 标题更新: {'是' if shared_store.get('title') else '否'}")
        logger.info(f"   📄 内容更新: {'是' if shared_store.get('content') else '否'}")

    def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始新闻分析流程完整测试")
        logger.info(f"⏰ 测试开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 设置流程
        if not self.setup_flow():
            logger.error("❌ 流程设置失败，无法继续测试")
            return

        # 创建测试文章
        test_articles = self.create_test_articles()

        # 定义测试用例
        test_cases = [
            (test_articles[0], "股票特定新闻测试 - 沪上阿姨"),
            # (test_articles[1], "股票特定新闻测试 - 平安银行"),
            # (test_articles[2], "行业导向新闻测试 - 人工智能"),
            # (test_articles[3], "行业导向新闻测试 - 新能源汽车"),
            # (test_articles[4], "行业导向新闻测试 - 生物医药")
        ]

        # 执行测试
        for article, test_name in test_cases:
            test_result = self.test_single_article(article, test_name)
            self.test_results.append(test_result)

        # 输出总结
        self._print_summary()

        # 记录日志文件信息
        logger.info(f"\n📄 完整测试日志已保存到: {self.log_filepath}")

    def _print_summary(self):
        """打印测试总结"""
        logger.info(f"\n{'='*100}")
        logger.info("📊 测试总结报告")
        logger.info(f"{'='*100}")

        total_tests = len(self.test_results)
        successful_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - successful_tests

        logger.info("📈 总体统计:")
        logger.info(f"   总测试数: {total_tests}")
        logger.info(f"   成功测试: {successful_tests} ✅")
        logger.info(f"   失败测试: {failed_tests} ❌")
        logger.info(f"   成功率: {(successful_tests/total_tests*100):.1f}%")

        if successful_tests > 0:
            avg_time = sum(r['execution_time'] for r in self.test_results if r['success']) / successful_tests
            logger.info(f"   平均执行时间: {avg_time:.2f}秒")

        logger.info("\n📋 详细结果:")
        for i, result in enumerate(self.test_results, 1):
            status = "✅" if result['success'] else "❌"
            time_str = f"{result['execution_time']:.2f}s" if result['success'] else "失败"
            analysis_type = result.get('analysis_type', '未知')

            logger.info(f"   {i}. {status} {result['test_name']} ({time_str}) - {analysis_type}")

            if not result['success'] and result['error']:
                logger.info(f"      错误: {result['error']}")

            if result['success']:
                stocks_count = len(result.get('mentioned_stocks', []))
                industries_count = len(result.get('mentioned_industries', []))
                logger.info(f"      股票: {stocks_count}只, 行业: {industries_count}个")

        # 功能验证
        logger.info("\n🔍 功能验证:")
        stock_specific_tests = [r for r in self.test_results if r.get('analysis_type') == 'stock_specific' and r['success']]
        industry_focused_tests = [r for r in self.test_results if r.get('analysis_type') == 'industry_focused' and r['success']]

        logger.info(f"   股票特定分析: {len(stock_specific_tests)} 项通过")
        logger.info(f"   行业导向分析: {len(industry_focused_tests)} 项通过")

        if stock_specific_tests:
            total_stocks = sum(len(r.get('mentioned_stocks', [])) for r in stock_specific_tests)
            logger.info(f"   检测到股票总数: {total_stocks} 只")

        if industry_focused_tests:
            total_industries = sum(len(r.get('mentioned_industries', [])) for r in industry_focused_tests)
            logger.info(f"   检测到行业总数: {total_industries} 个")

        logger.info(f"\n⏰ 测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"📄 日志文件: {self.log_filepath}")
        logger.info(f"{'='*100}")


def main():
    """主函数"""
    try:
        # 创建测试器
        tester = NewsAnalysisFlowTester()

        # 运行所有测试
        tester.run_all_tests()

        # 根据测试结果确定退出码
        failed_count = sum(1 for result in tester.test_results if not result['success'])
        if failed_count > 0:
            logger.warning(f"⚠️  有 {failed_count} 个测试失败")
            sys.exit(1)
        else:
            logger.info("🎉 所有测试都成功通过！")
            sys.exit(0)

    except KeyboardInterrupt:
        logger.info("\n⏹️  测试被用户中断")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ 测试执行过程中发生意外错误: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
