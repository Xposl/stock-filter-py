#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AKShare 行业板块数据提供者
用于获取行业板块的成分股信息，替代LLM推荐方式
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import akshare as ak

logger = logging.getLogger(__name__)

class AKShareIndustryProvider:
    """AKShare行业板块数据提供者"""
    
    def __init__(self):
        """初始化提供者"""
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # 行业关键词映射到AKShare板块名称
        self.industry_mapping = {
            # 科技行业
            "人工智能": ["人工智能", "计算机设备", "软件开发", "互联网服务"],
            "5G": ["5G概念", "通信设备", "通信服务", "电信运营"],
            "半导体": ["半导体", "电子元件", "芯片概念", "集成电路"],
            "新能源": ["新能源", "锂电池", "光伏概念", "风电概念"],
            "新能源汽车": ["新能源车", "汽车零部件", "动力电池", "充电桩"],
            "医疗": ["医疗器械", "医药生物", "生物疫苗", "中药概念"],
            "电商": ["电子商务", "互联网服务", "在线教育", "数字经济"],
            
            # 传统行业
            "房地产": ["房地产", "建筑装饰", "建筑材料", "水泥建材"],
            "银行": ["银行", "证券", "保险", "多元金融"],
            "钢铁": ["钢铁行业", "有色金属", "建筑材料", "基础化工"],
            "煤炭": ["煤炭开采", "石油石化", "天然气", "公用事业"],
            "食品": ["食品饮料", "农林牧渔", "酿酒行业", "食品加工"],
            "纺织": ["纺织服装", "服装家纺", "轻工制造", "造纸印刷"],
            
            # 消费行业
            "旅游": ["旅游酒店", "餐饮行业", "航空机场", "交通运输"],
            "零售": ["商业百货", "专业零售", "连锁经营", "商贸代理"],
            "家电": ["家用电器", "家具家居", "装饰材料", "智能家居"],
            "汽车": ["汽车整车", "汽车零部件", "汽车销售", "汽车服务"],
            
            # 其他行业
            "环保": ["环保工程", "水务处理", "固废处理", "大气治理"],
            "军工": ["国防军工", "航空航天", "船舶制造", "兵器装备"],
            "教育": ["在线教育", "教育培训", "出版传媒", "文化娱乐"],
        }
    
    async def get_industry_stocks(self, industry: str, impact_type: str, impact_degree: int) -> List[Dict]:
        """
        获取特定行业的代表性股票
        
        Args:
            industry: 行业名称
            impact_type: 影响类型
            impact_degree: 影响程度 (1-10)
            
        Returns:
            股票列表
        """
        try:
            logger.info(f"开始获取行业股票: {industry}")
            
            # 1. 获取行业板块名称
            board_names = self._map_industry_to_boards(industry)
            if not board_names:
                logger.warning(f"未找到行业 {industry} 对应的板块映射")
                return []
            
            # 2. 获取板块成分股
            all_stocks = []
            for board_name in board_names:
                stocks = await self._get_board_constituent_stocks(board_name)
                if stocks:
                    all_stocks.extend(stocks)
                    logger.info(f"板块 {board_name} 获取到 {len(stocks)} 只股票")
            
            if not all_stocks:
                logger.warning(f"行业 {industry} 未获取到成分股")
                return []
            
            # 3. 去重并排序
            unique_stocks = self._deduplicate_and_rank_stocks(all_stocks, impact_degree)
            
            # 4. 添加行业信息
            for stock in unique_stocks:
                stock.update({
                    "industry": industry,
                    "impact_type": impact_type,
                    "impact_degree": impact_degree,
                    "data_source": "akshare"
                })
            
            logger.info(f"行业 {industry} 最终返回 {len(unique_stocks)} 只股票")
            return unique_stocks[:10]  # 限制返回数量
            
        except Exception as e:
            logger.error(f"获取行业 {industry} 股票失败: {e}")
            return []
    
    def _map_industry_to_boards(self, industry: str) -> List[str]:
        """将行业名称映射到板块名称"""
        # 直接匹配
        if industry in self.industry_mapping:
            return self.industry_mapping[industry]
        
        # 模糊匹配
        for key, boards in self.industry_mapping.items():
            if industry in key or key in industry:
                return boards
        
        # 如果没有映射，直接使用行业名称
        return [industry]
    
    async def _get_board_constituent_stocks(self, board_name: str) -> List[Dict]:
        """获取板块成分股"""
        try:
            # 异步执行AKShare函数
            loop = asyncio.get_event_loop()
            
            # 1. 先获取板块名称列表
            board_names_df = await loop.run_in_executor(
                self.executor, 
                ak.stock_board_industry_name_em
            )
            
            # 查找匹配的板块
            matched_boards = board_names_df[
                board_names_df['板块名称'].str.contains(board_name, na=False)
            ]
            
            if matched_boards.empty:
                logger.warning(f"未找到板块: {board_name}")
                return []
            
            # 使用第一个匹配的板块
            actual_board_name = matched_boards.iloc[0]['板块名称']
            logger.debug(f"使用板块名称: {actual_board_name}")
            
            # 2. 获取板块成分股
            constituent_df = await loop.run_in_executor(
                self.executor,
                ak.stock_board_industry_cons_em,
                actual_board_name
            )
            
            if constituent_df.empty:
                logger.warning(f"板块 {actual_board_name} 成分股为空")
                return []
            
            # 3. 转换为标准格式
            stocks = []
            for _, row in constituent_df.iterrows():
                stock = {
                    "code": row.get('代码', ''),
                    "name": row.get('名称', ''),
                    "reason": f"{actual_board_name}板块成分股",
                    "relevance_score": self._calculate_relevance_score(row),
                    "board_name": actual_board_name,
                    "latest_price": row.get('最新价', 0),
                    "change_pct": row.get('涨跌幅', 0),
                    "market_cap": row.get('总市值', 0),
                    "turnover_rate": row.get('换手率', 0)
                }
                
                # 只添加有效的股票代码
                if stock["code"] and len(stock["code"]) == 6:
                    stocks.append(stock)
            
            logger.info(f"板块 {actual_board_name} 获取到 {len(stocks)} 只有效股票")
            return stocks
            
        except Exception as e:
            logger.error(f"获取板块 {board_name} 成分股失败: {e}")
            return []
    
    def _calculate_relevance_score(self, row: Dict) -> int:
        """计算股票关联度评分"""
        try:
            # 基础分数
            score = 5
            
            # 市值加分 (大市值股票更稳定)
            market_cap = float(row.get('总市值', 0))
            if market_cap > 1000_0000_0000:  # 千亿市值
                score += 3
            elif market_cap > 500_0000_0000:  # 五百亿市值
                score += 2
            elif market_cap > 100_0000_0000:  # 百亿市值
                score += 1
            
            # 换手率适中加分 (太高太低都不好)
            turnover_rate = float(row.get('换手率', 0))
            if 2 <= turnover_rate <= 10:
                score += 1
            
            # 价格稳定性加分 (涨跌幅适中)
            change_pct = abs(float(row.get('涨跌幅', 0)))
            if change_pct < 5:  # 涨跌幅小于5%
                score += 1
            
            return min(score, 10)  # 最高10分
            
        except Exception:
            return 5  # 默认分数
    
    def _deduplicate_and_rank_stocks(self, stocks: List[Dict], impact_degree: int) -> List[Dict]:
        """去重并按相关性排序股票"""
        # 按股票代码去重，保留评分最高的
        unique_stocks = {}
        for stock in stocks:
            code = stock.get("code", "")
            if code:
                if code not in unique_stocks or stock.get("relevance_score", 0) > unique_stocks[code].get("relevance_score", 0):
                    unique_stocks[code] = stock
        
        # 按相关性和影响程度排序
        sorted_stocks = sorted(
            unique_stocks.values(),
            key=lambda x: (
                x.get("relevance_score", 0) * impact_degree,
                x.get("market_cap", 0)
            ),
            reverse=True
        )
        
        return sorted_stocks
    
    async def get_available_industries(self) -> List[str]:
        """获取可用的行业列表"""
        try:
            loop = asyncio.get_event_loop()
            board_names_df = await loop.run_in_executor(
                self.executor,
                ak.stock_board_industry_name_em
            )
            
            return board_names_df['板块名称'].tolist()
            
        except Exception as e:
            logger.error(f"获取行业列表失败: {e}")
            return list(self.industry_mapping.keys())
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)


# 全局实例
akshare_industry_provider = AKShareIndustryProvider()

# 便捷函数
async def get_industry_stocks_from_akshare(industry: str, impact_type: str, impact_degree: int) -> List[Dict]:
    """便捷函数：获取行业股票"""
    return await akshare_industry_provider.get_industry_stocks(industry, impact_type, impact_degree) 