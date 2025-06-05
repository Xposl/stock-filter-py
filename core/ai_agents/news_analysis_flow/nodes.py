import logging
from typing import Any, Dict, List
from pocketflow import Node

from core.models.news_article import NewsArticle
from ..llm_clients.qwen_client import QwenLLMClient
from core.data_providers.stock_data_factory import get_industry_stocks

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NewsClassifierNode(Node):
    """使用大模型进行新闻分类和股票检测"""
    def prep(self, shared):
        return shared['article']

    def exec(self, article: NewsArticle|None):
        if not article:
          return {
            "analysis_type": "unknown",
            "confidence": 0,
            "reason": "LLM分析",
            "content": None,
            "mentioned_stocks": [],
            "mentioned_industries": {"hk": [], "us": [], "zh": []},
            "markets": []
          }
        content = article.get_analysis_content()
        # 构建分类提示词
        prompt = f"""请分析以下新闻内容，判断其类型并提取股票信息, 或者可能的概念，行业，最多返回3个，同时判断影响的市场：
标题：{article.title}
内容：{content[:1000]}...

请按以下格式返回JSON结果：
{{
    "analysis_type": "stock_specific" 或 "industry_focused",
    "confidence": 0.0-1.0之间的置信度,
    "reason": "判断理由",
    "markets": ["hk", "us", "zh"] - 影响的市场（港股、美股、A股），
    "mentioned_stocks": [
      {{"name": "股票名称", "code": "股票代码", "market": "hk/us/zh"}}
    ],
    "mentioned_industries": {{
        "hk": ["行业名称1", "行业名称2"],
        "us": ["行业名称1", "行业名称2"], 
        "zh": ["行业名称1", "行业名称2"]
    }}
}}

分类标准：
- stock_specific: 明确提及具体股票名称和代码的新闻
- industry_focused: 主要讨论行业、主题、政策等的新闻

市场判断标准：
- hk: 港股市场，股票代码如00700、03690等，或提及港交所、恒生指数
- us: 美股市场，股票代码如AAPL、TSLA等，或提及纳斯达克、标普500
- zh: A股市场，股票代码如600000、000001等，或提及上交所、深交所、沪深300

请重点关注标题和内容中是否包含"公司名(代码)"格式的股票信息，并准确判断所属市场。
对于mentioned_industries，请根据新闻内容涉及的行业影响不同市场进行分类。"""

        try:
            qwen_client = QwenLLMClient()
            # 🔥 使用正确的同步调用方法
            response = qwen_client.chat_completions_create(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
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
                mentioned_stocks = result.get("mentioned_stocks", [])
                markets = result.get("markets", [])
                mentioned_industries = result.get("mentioned_industries", {})
                
                # 🔄 确保mentioned_industries是字典格式，如果是列表则转换
                if isinstance(mentioned_industries, list):
                    # 如果LLM返回的是列表格式，根据markets分配到对应市场
                    industries_dict = {"hk": [], "us": [], "zh": []}
                    if markets:
                        # 将行业分配给检测到的市场
                        for market in markets:
                            if market in industries_dict:
                                industries_dict[market] = mentioned_industries.copy()
                    else:
                        # 默认分配给A股市场
                        industries_dict["zh"] = mentioned_industries.copy()
                    mentioned_industries = industries_dict
                else:
                    # 确保字典格式完整
                    mentioned_industries = {
                        "hk": mentioned_industries.get("hk", []),
                        "us": mentioned_industries.get("us", []), 
                        "zh": mentioned_industries.get("zh", [])
                    }
                
                # 确保每只股票都有market字段，如果没有则根据markets推断
                for stock in mentioned_stocks:
                    if isinstance(stock, dict) and "market" not in stock:
                        # 根据代码或markets列表推断市场
                        code = stock.get("code", "")
                        if code.isdigit():
                            if len(code) == 5:  # 港股格式
                                stock["market"] = "hk"
                            elif len(code) == 6:  # A股格式
                                stock["market"] = "zh"
                        elif code.isalpha():  # 美股格式
                            stock["market"] = "us"
                        elif markets:  # 使用检测到的市场
                            stock["market"] = markets[0]
                        else:
                            stock["market"] = "zh"  # 默认A股
                
                return {
                    "analysis_type": result.get("analysis_type", "industry_focused"),
                    "confidence": max(0.0, min(1.0, float(result.get("confidence", 0.8)))),
                    "reason": result.get("reason", "LLM分析"),
                    "mentioned_stocks": mentioned_stocks,
                    "mentioned_industries": mentioned_industries,
                    "markets": markets,
                    "content": content
                }
            else:
                logger.warning(f"LLM返回结果无法解析为JSON，原始内容: {response_text[:500]}")
                return {
                    "analysis_type": "unknown",
                    "confidence": 0,
                    "reason": "LLM分析",
                    "mentioned_stocks": [],
                    "mentioned_industries": {"hk": [], "us": [], "zh": []},
                    "markets": [],
                    "content": content
                }
                
        except Exception as e:
            logger.error(f"LLM分类失败: {e}，使用默认分类")
            return {
              "analysis_type": "unknown",
              "confidence": 0,
              "reason": "LLM分析",
              "mentioned_stocks": [],
              "mentioned_industries": {"hk": [], "us": [], "zh": []},
              "markets": [],
              "content": content
            }

    def post(self, shared, prep_res, exec_res):
        shared['title'] = prep_res.title if hasattr(prep_res, 'title') else prep_res.get('title', '')
        shared['content'] = exec_res['content']
        shared['mentioned_stocks'] = exec_res['mentioned_stocks']
        shared['mentioned_industries'] = exec_res['mentioned_industries']
        shared['markets'] = exec_res['markets']  # 存储影响的市场信息

        if exec_res['analysis_type'] == 'stock_specific':
          return 'stock_specific'
        elif exec_res['analysis_type'] == 'industry_focused':
          return 'industry_focused'
        else:
          return 'unknown'
  
class TickerIndustryFinderNode(Node):
    """通过行业搜索可能的股票池"""
    def prep(self, shared):
        return {
            'mentioned_industries': shared['mentioned_industries'],
            'markets': shared.get('markets', ['zh'])  # 默认A股市场
        }

    def exec(self, data):
        """
        基于新闻提及的行业和市场，通过不同数据源获取相关概念股
        
        Args:
            data: 包含行业列表和市场信息的字典
                - mentioned_industries: 新闻中提及的行业字典 {"hk": [...], "us": [...], "zh": [...]}
                - markets: 影响的市场列表 ['hk', 'us', 'zh']
            
        Returns:
            概念股票列表
        """
        mentioned_industries = data.get('mentioned_industries', {"hk": [], "us": [], "zh": []})
        markets = data.get('markets', ['zh'])
        
        logger.info(f"🔍 开始搜索行业概念股")
        logger.info(f"🏢 影响市场: {markets}")
        logger.info(f"📊 行业分布: {mentioned_industries}")
        
        # 检查是否有任何行业被提及
        total_industries = sum(len(industries) for industries in mentioned_industries.values())
        if total_industries == 0:
            logger.info("未提及任何行业，跳过概念股搜索")
            return []
        
        # 存储所有概念股
        all_concept_stocks = []
        
        # 🔥 处理A股市场行业（使用akshare）
        zh_industries = mentioned_industries.get('zh', [])
        if zh_industries:
            logger.info(f"🇨🇳 处理A股行业: {zh_industries}")
            for industry in zh_industries:
                try:
                    # 🔥 使用异步方式调用get_industry_stocks
                    import asyncio
                    
                    # 检查是否已有事件循环
                    try:
                        loop = asyncio.get_running_loop()
                        # 如果有运行中的循环，使用run_in_executor
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, self._get_zh_industry_stocks(industry))
                            zh_stocks = future.result(timeout=30)  # 30秒超时
                    except RuntimeError:
                        # 没有运行中的循环，直接使用asyncio.run
                        zh_stocks = asyncio.run(self._get_zh_industry_stocks(industry))
                    
                    if zh_stocks:
                        # 为A股股票添加市场标识
                        for stock in zh_stocks:
                            stock['market'] = 'zh'
                            stock['source'] = 'akshare_industry'
                            stock['source_industry'] = industry
                        
                        all_concept_stocks.extend(zh_stocks)
                        logger.info(f"  ✅ A股行业 {industry} 获取到 {len(zh_stocks)} 只股票")
                    else:
                        logger.warning(f"  ⚠️ A股行业 {industry} 未获取到股票")
                        
                except Exception as e:
                    logger.error(f"  ❌ A股行业 {industry} 获取失败: {e}")
        
        # 🔥 处理港股市场行业（暂时跳过，akshare主要支持A股）
        hk_industries = mentioned_industries.get('hk', [])
        if hk_industries:
            logger.info(f"🇭🇰 港股行业暂不支持: {hk_industries}")
            # TODO: 未来可以扩展支持港股行业查询
        
        # 🔥 处理美股市场行业（暂时跳过，akshare主要支持A股）  
        us_industries = mentioned_industries.get('us', [])
        if us_industries:
            logger.info(f"🇺🇸 美股行业暂不支持: {us_industries}")
            # TODO: 未来可以扩展支持美股行业查询

        # 🔥 对获取的股票进行去重和排序
        if all_concept_stocks:
            unique_stocks = self._deduplicate_stocks(all_concept_stocks)
            sorted_stocks = self._sort_stocks_by_relevance(unique_stocks)
            
            logger.info(f"🎯 行业概念股搜索完成，共获取 {len(sorted_stocks)} 只去重后的股票")
            return sorted_stocks[:20]  # 限制最多返回20只股票
        else:
            logger.info("🔍 未获取到任何行业概念股")
            return []
    
    async def _get_zh_industry_stocks(self, industry: str) -> List[Dict]:
        """
        异步获取A股特定行业的股票
        
        Args:
            industry: 行业名称
            
        Returns:
            股票列表
        """
        try:
            # 🔥 调用akshare行业数据获取函数
            stocks = await get_industry_stocks(
                industry=industry,
                impact_type="positive",  # 正面影响
                impact_degree=7,  # 影响程度7/10
                limit=15  # 每个行业最多15只股票
            )
            
            if stocks:
                logger.debug(f"行业 {industry} 从akshare获取到 {len(stocks)} 只股票")
                return stocks
            else:
                logger.warning(f"行业 {industry} 未从akshare获取到股票")
                return []
                
        except Exception as e:
            logger.error(f"获取A股行业 {industry} 股票失败: {e}")
            return []
    
    def _deduplicate_stocks(self, stocks: List[Dict]) -> List[Dict]:
        """
        股票去重，保留评分最高的
        
        Args:
            stocks: 股票列表
            
        Returns:
            去重后的股票列表
        """
        unique_stocks = {}
        for stock in stocks:
            code = stock.get('code', '')
            if code:
                # 如果股票代码已存在，保留评分更高的
                if (code not in unique_stocks or 
                    stock.get('relevance_score', 0) > unique_stocks[code].get('relevance_score', 0)):
                    unique_stocks[code] = stock
        
        return list(unique_stocks.values())
    
    def _sort_stocks_by_relevance(self, stocks: List[Dict]) -> List[Dict]:
        """
        按相关性排序股票
        
        Args:
            stocks: 股票列表
            
        Returns:
            排序后的股票列表
        """
        return sorted(
            stocks,
            key=lambda x: (
                x.get('relevance_score', 0),      # 优先按相关性评分
                x.get('market_cap', 0),          # 然后按市值
                -x.get('change_pct', 0)          # 最后按涨跌幅（负值表示跌幅小的优先）
            ),
            reverse=True
        )

    def post(self, shared, prep_res, exec_res):
        """
        将获取的概念股存储到共享数据中
        """
        # 将概念股存储到共享数据
        shared['concept_stocks'] = exec_res if exec_res else []
        
        # 合并到总的股票列表中
        all_stocks = shared.get('mentioned_stocks', []).copy()
        
        # 添加概念股，避免重复
        existing_codes = {stock.get('code') for stock in all_stocks if isinstance(stock, dict)}
        for concept_stock in shared['concept_stocks']:
            if concept_stock.get('code') not in existing_codes:
                # 转换为标准格式
                all_stocks.append({
                    'name': concept_stock.get('name'),
                    'code': concept_stock.get('code'),
                    'market': concept_stock.get('market', 'zh'),
                    'source': 'industry_concept',
                    'relevance_score': concept_stock.get('relevance_score', 5),
                    'source_industry': concept_stock.get('source_industry'),
                    'reason': concept_stock.get('reason', '行业概念股')
                })
        
        shared['mentioned_stocks'] = all_stocks
        
        logger.info(f"📊 概念股后处理完成，总股票数: {len(all_stocks)}")
        return 'default'
    
class TickerScoreUpdate(Node):
    """更新股票评分"""
    def prep(self, shared):
        return shared['mentioned_stocks']

    def exec(self, mentioned_stocks):
        """
        使用DataSourceHelper更新股票的评分和分析数据
        
        Args:
            mentioned_stocks: 股票列表
            
        Returns:
            更新后的股票数据
        """
        logger.info(f"🔍 开始更新 {len(mentioned_stocks)} 只股票的评分")
        
        if not mentioned_stocks:
            logger.info("没有股票需要更新评分")
            return []
        
        from core.data_source_helper import DataSourceHelper
        
        updated_stocks = []
        data_helper = DataSourceHelper()
        
        for i, stock in enumerate(mentioned_stocks, 1):
            stock_code = stock.get('code') if isinstance(stock, dict) else None
            stock_name = stock.get('name') if isinstance(stock, dict) else None
            
            if not stock_code:
                logger.warning(f"  ⚠️ 第{i}只股票缺少代码信息，跳过")
                continue
            
            logger.info(f"  📈 [{i}/{len(mentioned_stocks)}] 更新股票: {stock_name} ({stock_code})")
            
            try:
                # 使用DataSourceHelper获取股票数据和评分
                ticker_data, kl_data, score_data = data_helper.get_ticker_data(
                    code= data_helper.get_ticker_code(stock['market'], stock_code),
                    days=600  # 获取600天的历史数据用于分析
                )
                
                # 检查ticker_data是否为None（股票不存在于数据库中）
                if ticker_data is None:
                    logger.warning(f"    ⚠️ 股票 {stock_code} 在数据库中不存在，保留原始信息")
                    # 保留原始股票信息，标记为未更新
                    original_stock = stock.copy() if isinstance(stock, dict) else {
                        'code': stock_code,
                        'name': stock_name
                    }
                    original_stock.update({
                        'data_updated': False,
                        'error_reason': '股票在数据库中不存在'
                    })
                    updated_stocks.append(original_stock)
                    continue
                
                # 检查是否有有效的评分数据
                if score_data:
                    # 获取最新评分
                    latest_score = score_data[0] if score_data else None
                    
                    # 更新股票信息
                    updated_stock = stock.copy() if isinstance(stock, dict) else {
                        'code': stock_code,
                        'name': stock_name
                    }
                    
                    # 添加评分和分析数据
                    updated_stock.update({
                        'ticker_id': ticker_data.id,
                        'ticker_name': ticker_data.name,
                        'ticker_group_id': ticker_data.group_id,
                        'ticker_status': ticker_data.status,
                        'score': latest_score.score if latest_score else None,
                        'score_time': latest_score.time_key if latest_score else None,
                        'score_id': latest_score.id if latest_score else None,
                        'kline_days': len(kl_data) if kl_data else 0,
                        'data_updated': True,
                        'update_timestamp': '2024-01-27'  # 简单的时间戳
                    })
                    
                    updated_stocks.append(updated_stock)
                    
                    logger.info(f"    ✅ 更新成功 - 评分: {latest_score.score if latest_score else 'N/A'}, "
                              f"K线数据: {len(kl_data) if kl_data else 0} 天")
                    
                else:
                    logger.warning(f"    ⚠️ 未获取到评分数据，保留原始信息")
                    # 保留原始股票信息，标记为未更新
                    original_stock = stock.copy() if isinstance(stock, dict) else {
                        'code': stock_code,
                        'name': stock_name
                    }
                    original_stock.update({
                        'ticker_id': ticker_data.id if ticker_data else None,
                        'ticker_name': ticker_data.name if ticker_data else stock_name,
                        'data_updated': False,
                        'error_reason': '未获取到评分数据'
                    })
                    updated_stocks.append(original_stock)
                    
            except Exception as e:
                logger.error(f"    ❌ 更新股票 {stock_code} 失败: {e}")
                # 保留原始股票信息，记录错误
                error_stock = stock.copy() if isinstance(stock, dict) else {
                    'code': stock_code,
                    'name': stock_name
                }
                error_stock.update({
                    'data_updated': False,
                    'error_reason': str(e)
                })
                updated_stocks.append(error_stock)
        
        logger.info(f"🎯 股票评分更新完成，成功更新: "
                   f"{sum(1 for s in updated_stocks if s.get('data_updated', False))}/{len(updated_stocks)} 只")
        
        return updated_stocks

    def post(self, shared, prep_res, exec_res):
        """
        将更新后的股票数据存储回共享存储
        """
        # 更新共享存储中的股票数据
        shared['mentioned_stocks'] = exec_res if exec_res else []
        shared['stocks_with_scores'] = [
            stock for stock in exec_res 
            if stock.get('data_updated', False) and stock.get('score') is not None
        ]
        
        # 统计信息
        total_stocks = len(exec_res) if exec_res else 0
        updated_stocks = sum(1 for s in exec_res if s.get('data_updated', False)) if exec_res else 0
        scored_stocks = len(shared['stocks_with_scores'])
        
        logger.info(f"📊 评分更新后处理完成:")
        logger.info(f"  - 总股票数: {total_stocks}")
        logger.info(f"  - 成功更新: {updated_stocks}")
        logger.info(f"  - 有评分数据: {scored_stocks}")
        
        return 'default'
    
class TickerAnalysisNode(Node):
    """分析股票"""
    def prep(self, shared):
        return shared['mentioned_stocks']

    def exec(self, mentioned_stocks):
        print('🔍 分析股票')
        print(mentioned_stocks)

    def post(self, shared, prep_res, exec_res):
        return 'default'