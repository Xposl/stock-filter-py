#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AKShare 行业板块数据提供者
用于获取行业板块的成分股信息，支持动态板块获取和全市场分类
集成到统一的data_providers架构中
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Set
from concurrent.futures import ThreadPoolExecutor
import akshare as ak
import pandas as pd
from datetime import datetime

from .stock_data_provider import StockDataProvider, StockMarket

logger = logging.getLogger(__name__)

class AKShareIndustryProvider(StockDataProvider):
    """AKShare行业板块数据提供者，继承统一的数据提供者接口"""
    
    def __init__(self):
        """初始化提供者"""
        super().__init__(name="AKShare Industry Provider", priority=90)
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # 缓存动态获取的板块信息
        self._board_cache: Optional[pd.DataFrame] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = 3600  # 缓存1小时
        
        # 行业关键词映射 - 用于模糊匹配 (基于实际AKShare板块名称)
        self.industry_keywords = {
            # 科技行业 - 根据实际板块名称映射
            "人工智能": ["半导体", "软件开发", "计算机设备", "电子元件"],
            "AI": ["半导体", "软件开发", "计算机设备"], 
            "5G": ["通信设备", "通信服务", "电子元件"],
            "半导体": ["半导体"],
            "芯片": ["半导体", "电子元件"],
            "新能源": ["电池", "光伏设备", "风电设备", "能源金属"],
            "新能源汽车": ["电池", "汽车整车", "汽车零部件"],
            "电动车": ["电池", "汽车整车", "汽车零部件"],
            "医疗": ["医疗器械", "医疗服务", "医药商业", "化学制药", "生物制品", "中药"],
            "生物医药": ["生物制品", "化学制药", "医疗器械"],
            "电商": ["互联网服务", "商业百货"],
            
            # 传统行业
            "房地产": ["房地产开发", "房地产服务"],
            "银行": ["银行", "证券", "保险", "多元金融"],
            "钢铁": ["钢铁行业", "有色金属"],
            "煤炭": ["煤炭行业", "石油行业", "化学原料"],
            "食品": ["食品饮料", "农牧饲渔", "酿酒行业"],
            "纺织": ["纺织服装", "化纤行业"],
            
            # 消费行业
            "旅游": ["旅游酒店", "航空机场", "航运港口"],
            "零售": ["商业百货", "贸易行业"],
            "家电": ["家电行业", "家用轻工", "消费电子"],
            "汽车": ["汽车整车", "汽车零部件", "汽车服务"],
            
            # 其他行业
            "环保": ["环保行业", "公用事业"],
            "军工": ["航天航空", "船舶制造"],
            "教育": ["教育", "文化传媒"],
        }
    
    async def get_all_industry_boards(self) -> pd.DataFrame:
        """动态获取所有行业板块信息"""
        try:
            # 检查缓存
            now = datetime.now()
            if (self._board_cache is not None and 
                self._cache_timestamp is not None and 
                (now - self._cache_timestamp).seconds < self._cache_ttl):
                logger.debug("使用缓存的板块信息")
                return self._board_cache
            
            # 获取最新板块信息
            logger.info("开始获取AKShare行业板块信息")
            loop = asyncio.get_event_loop()
            board_df = await loop.run_in_executor(
                self.executor, 
                ak.stock_board_industry_name_em
            )
            
            # 更新缓存
            self._board_cache = board_df
            self._cache_timestamp = now
            
            logger.info(f"成功获取 {len(board_df)} 个行业板块")
            return board_df
            
        except Exception as e:
            logger.error(f"获取行业板块信息失败: {e}")
            self._handle_error(e, "获取行业板块信息")
            return pd.DataFrame()
    
    async def get_industry_stocks(self, industry: str, impact_type: str = "positive", 
                                impact_degree: int = 5, limit: int = 10) -> List[Dict]:
        """
        获取特定行业的代表性股票
        
        Args:
            industry: 行业名称
            impact_type: 影响类型
            impact_degree: 影响程度 (1-10)
            limit: 返回股票数量限制
            
        Returns:
            股票列表
        """
        try:
            logger.info(f"开始获取行业股票: {industry}")
            
            # 1. 动态获取匹配的板块
            matched_boards = await self._find_matching_boards(industry)
            if not matched_boards:
                logger.warning(f"未找到行业 {industry} 对应的板块")
                return []
            
            # 2. 获取板块成分股
            all_stocks = []
            for board_name in matched_boards[:3]:  # 限制最多3个板块
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
                    "data_source": "akshare_industry"
                })
            
            result = unique_stocks[:limit]
            logger.info(f"行业 {industry} 最终返回 {len(result)} 只股票")
            return result
            
        except Exception as e:
            logger.error(f"获取行业 {industry} 股票失败: {e}")
            self._handle_error(e, f"获取行业{industry}股票")
            return []
    
    async def _find_matching_boards(self, industry: str) -> List[str]:
        """查找匹配的板块名称"""
        try:
            board_df = await self.get_all_industry_boards()
            if board_df.empty:
                return []
            
            matched_boards = []
            
            # 1. 精确匹配
            exact_matches = board_df[board_df['板块名称'] == industry]
            if not exact_matches.empty:
                matched_boards.extend(exact_matches['板块名称'].tolist())
            
            # 2. 包含匹配
            if not matched_boards:
                contains_matches = board_df[board_df['板块名称'].str.contains(industry, na=False)]
                if not contains_matches.empty:
                    matched_boards.extend(contains_matches['板块名称'].tolist())
            
            # 3. 关键词模糊匹配
            if not matched_boards and industry in self.industry_keywords:
                keywords = self.industry_keywords[industry]
                for keyword in keywords:
                    keyword_matches = board_df[board_df['板块名称'].str.contains(keyword, na=False)]
                    if not keyword_matches.empty:
                        matched_boards.extend(keyword_matches['板块名称'].tolist())
            
            # 去重并限制数量
            matched_boards = list(dict.fromkeys(matched_boards))  # 保持顺序去重
            
            logger.debug(f"行业 {industry} 匹配到板块: {matched_boards}")
            return matched_boards
            
        except Exception as e:
            logger.error(f"查找匹配板块失败: {e}")
            return []
    
    async def _get_board_constituent_stocks(self, board_name: str) -> List[Dict]:
        """获取板块成分股"""
        try:
            loop = asyncio.get_event_loop()
            
            # 获取板块成分股
            constituent_df = await loop.run_in_executor(
                self.executor,
                ak.stock_board_industry_cons_em,
                board_name
            )
            
            if constituent_df.empty:
                logger.warning(f"板块 {board_name} 成分股为空")
                return []
            
            # 转换为标准格式
            stocks = []
            for _, row in constituent_df.iterrows():
                stock = {
                    "code": row.get('代码', ''),
                    "name": row.get('名称', ''),
                    "reason": f"{board_name}板块成分股",
                    "relevance_score": self._calculate_relevance_score(row),
                    "board_name": board_name,
                    "latest_price": float(row.get('最新价', 0)) if pd.notna(row.get('最新价')) else 0,
                    "change_pct": float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅')) else 0,
                    "market_cap": float(row.get('总市值', 0)) if pd.notna(row.get('总市值')) else 0,
                    "turnover_rate": float(row.get('换手率', 0)) if pd.notna(row.get('换手率')) else 0,
                    "volume": float(row.get('成交量', 0)) if pd.notna(row.get('成交量')) else 0,
                    "amount": float(row.get('成交额', 0)) if pd.notna(row.get('成交额')) else 0
                }
                
                # 只添加有效的股票代码
                if stock["code"] and len(stock["code"]) == 6:
                    stocks.append(stock)
            
            logger.debug(f"板块 {board_name} 获取到 {len(stocks)} 只有效股票")
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
            market_cap = float(row.get('总市值', 0)) if pd.notna(row.get('总市值')) else 0
            if market_cap > 1000_0000_0000:  # 千亿市值
                score += 3
            elif market_cap > 500_0000_0000:  # 五百亿市值
                score += 2
            elif market_cap > 100_0000_0000:  # 百亿市值
                score += 1
            
            # 换手率适中加分 (太高太低都不好)
            turnover_rate = float(row.get('换手率', 0)) if pd.notna(row.get('换手率')) else 0
            if 2 <= turnover_rate <= 10:
                score += 1
            
            # 价格稳定性加分 (涨跌幅适中)
            change_pct = abs(float(row.get('涨跌幅', 0))) if pd.notna(row.get('涨跌幅')) else 0
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
    
    async def get_all_industry_categories(self) -> Dict[str, List[str]]:
        """获取全市场的行业分类体系"""
        try:
            board_df = await self.get_all_industry_boards()
            if board_df.empty:
                return {}
            
            # 按行业特征进行分类
            categories = {
                "科技行业": [],
                "消费行业": [],
                "金融行业": [],
                "工业制造": [],
                "能源材料": [],
                "医疗健康": [],
                "房地产建筑": [],
                "公用事业": [],
                "农林牧渔": [],
                "新能源装备": [],  # 重命名避免冲突
                "交通运输": [],
                "轻工制造": [],
                "其他行业": []
            }
            
            # 分类关键词
            category_keywords = {
                "科技行业": ["半导体", "软件开发", "计算机设备", "电子元件", "通信设备", "通信服务", "互联网服务", "游戏"],
                "消费行业": ["商业百货", "食品饮料", "纺织服装", "家电行业", "汽车整车", "旅游酒店", "餐饮", "消费电子", "美容护理", "珠宝首饰"],
                "金融行业": ["银行", "证券", "保险", "多元金融"],
                "工业制造": ["专用设备", "通用设备", "工程机械", "电机", "电源设备", "工程建设", "工程咨询服务", "船舶制造", "航天航空", "仪器仪表"],
                "能源材料": ["煤炭行业", "石油行业", "电力行业", "钢铁行业", "有色金属", "化学原料", "化学制品", "小金属", "能源金属", "贵金属"],
                "医疗健康": ["医疗器械", "医疗服务", "医药商业", "化学制药", "生物制品", "中药"],
                "房地产建筑": ["房地产开发", "房地产服务", "工程建设", "装修建材", "装修装饰", "水泥建材", "玻璃玻纤"],
                "公用事业": ["公用事业", "燃气", "环保行业", "电网设备"],
                "农林牧渔": ["农牧饲渔", "农药兽药", "化肥行业"],
                "新能源装备": ["电池", "光伏设备", "风电设备"],  # 重命名避免冲突
                "交通运输": ["航空机场", "航运港口", "铁路公路", "物流行业", "交运设备"],
                "轻工制造": ["家用轻工", "包装材料", "塑料制品", "橡胶制品", "造纸印刷", "化纤行业", "非金属材料"]
            }
            
            # 分类板块
            for _, row in board_df.iterrows():
                board_name = row.get('板块名称', '')
                classified = False
                
                for category, keywords in category_keywords.items():
                    if any(keyword in board_name for keyword in keywords):
                        categories[category].append(board_name)
                        classified = True
                        break
                
                if not classified:
                    categories["其他行业"].append(board_name)
            
            # 移除空分类
            categories = {k: v for k, v in categories.items() if v}
            
            logger.info(f"全市场行业分类完成，共 {len(categories)} 个大类")
            return categories
            
        except Exception as e:
            logger.error(f"获取行业分类失败: {e}")
            return {}
    
    # 实现父类的抽象方法（可选，主要用于行业数据）
    def get_stock_info(self, symbol: str, market: StockMarket = None) -> Optional[Dict[str, Any]]:
        """获取股票基本信息（行业提供者不实现此方法）"""
        return None
    
    def get_stock_quote(self, symbol: str, market: StockMarket = None) -> Optional[Dict[str, Any]]:
        """获取股票实时行情（行业提供者不实现此方法）"""
        return None
    
    def get_stock_history(self, symbol: str, start_date, end_date=None, period=None, market=None):
        """获取股票历史数据（行业提供者不实现此方法）"""
        return None
    
    def get_company_info(self, symbol: str, market: StockMarket = None) -> Optional[Dict[str, Any]]:
        """获取公司详细信息（行业提供者不实现此方法）"""
        return None
    
    def search_stocks(self, keyword: str, market: StockMarket = None, limit: int = 10) -> List[Dict[str, Any]]:
        """按行业关键词搜索股票"""
        try:
            # 这里可以实现基于行业的股票搜索
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                stocks = loop.run_until_complete(self.get_industry_stocks(keyword, limit=limit))
                return stocks
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"按行业搜索股票失败: {e}")
            return []
    
    def get_supported_markets(self) -> List[StockMarket]:
        """获取支持的市场列表"""
        return [StockMarket.A_SHARE]  # 目前主要支持A股
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)


# 全局实例
akshare_industry_provider = AKShareIndustryProvider()

# 便捷函数
async def get_industry_stocks_from_akshare(industry: str, impact_type: str = "positive", 
                                         impact_degree: int = 5, limit: int = 10) -> List[Dict]:
    """便捷函数：获取行业股票"""
    return await akshare_industry_provider.get_industry_stocks(industry, impact_type, impact_degree, limit)

async def get_all_industry_categories() -> Dict[str, List[str]]:
    """便捷函数：获取全市场行业分类"""
    return await akshare_industry_provider.get_all_industry_categories() 