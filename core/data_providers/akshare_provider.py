"""
AKShare股票数据提供者
基于akshare库实现的股票数据获取
"""

import akshare as ak
import pandas as pd
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, date
import logging

from .stock_data_provider import StockDataProvider, StockMarket, DataPeriod

logger = logging.getLogger(__name__)


class AKShareProvider(StockDataProvider):
    """AKShare数据提供者"""
    
    def __init__(self):
        super().__init__(name="AKShare", priority=100)  # 最高优先级
        self._supported_markets = [
            StockMarket.A_SHARE,
            StockMarket.HONG_KONG,
            StockMarket.US
        ]
    
    def get_supported_markets(self) -> List[StockMarket]:
        """获取支持的市场列表"""
        return self._supported_markets
    
    def normalize_symbol(self, symbol: str, market: StockMarket = None) -> str:
        """标准化股票代码"""
        symbol = symbol.upper().strip()
        
        # 去除前缀
        if symbol.startswith('SH') or symbol.startswith('SZ'):
            symbol = symbol[2:]
        
        # 确保A股代码是6位数字
        if market == StockMarket.A_SHARE and symbol.isdigit():
            symbol = symbol.zfill(6)
        
        return symbol
    
    def _detect_market(self, symbol: str) -> StockMarket:
        """自动检测股票市场"""
        symbol = symbol.upper().strip()
        
        # A股检测
        if symbol.startswith('SH') or symbol.startswith('SZ'):
            return StockMarket.A_SHARE
        elif symbol.isdigit() and len(symbol) == 6:
            return StockMarket.A_SHARE
        elif symbol.startswith('0') or symbol.startswith('3'):  # 深圳股票
            return StockMarket.A_SHARE
        elif symbol.startswith('6'):  # 上海股票
            return StockMarket.A_SHARE
        
        # 港股检测
        elif symbol.isdigit() and len(symbol) <= 5:
            return StockMarket.HONG_KONG
        
        # 美股检测
        elif symbol.isalpha():
            return StockMarket.US
        
        return StockMarket.OTHER
    
    def get_stock_info(self, symbol: str, market: StockMarket = None) -> Optional[Dict[str, Any]]:
        """获取股票基本信息"""
        try:
            if market is None:
                market = self._detect_market(symbol)
            
            symbol = self.normalize_symbol(symbol, market)
            
            if market == StockMarket.A_SHARE:
                # 获取A股基本信息
                df = ak.stock_zh_a_spot_em()
                stock_info = df[df['代码'] == symbol]
                
                if stock_info.empty:
                    return None
                
                row = stock_info.iloc[0]
                return {
                    'symbol': symbol,
                    'name': row['名称'],
                    'market': 'A股',
                    'current_price': row['最新价'],
                    'change_percent': row['涨跌幅'],
                    'volume': row['成交量'],
                    'turnover': row['成交额'],
                    'pe_ratio': row.get('市盈率-动态', None),
                    'pb_ratio': row.get('市净率', None),
                    'total_value': row.get('总市值', None),
                    'circulation_value': row.get('流通市值', None)
                }
            
            elif market == StockMarket.HONG_KONG:
                # 获取港股基本信息
                df = ak.stock_hk_spot_em()
                stock_info = df[df['代码'] == symbol]
                
                if stock_info.empty:
                    return None
                
                row = stock_info.iloc[0]
                return {
                    'symbol': symbol,
                    'name': row['名称'],
                    'market': '港股',
                    'current_price': row['最新价'],
                    'change_percent': row['涨跌幅'],
                    'volume': row['成交量'],
                    'turnover': row['成交额'],
                    'total_value': row.get('总市值', None)
                }
            
            elif market == StockMarket.US:
                # 获取美股基本信息
                df = ak.stock_us_spot_em()
                stock_info = df[df['代码'] == symbol]
                
                if stock_info.empty:
                    return None
                
                row = stock_info.iloc[0]
                return {
                    'symbol': symbol,
                    'name': row['名称'],
                    'market': '美股',
                    'current_price': row['最新价'],
                    'change_percent': row['涨跌幅'],
                    'volume': row['成交量'],
                    'turnover': row.get('成交额', None)
                }
            
            return None
            
        except Exception as e:
            self._handle_error(e, "获取股票基本信息")
            return None
    
    def get_stock_quote(self, symbol: str, market: StockMarket = None) -> Optional[Dict[str, Any]]:
        """获取股票实时行情"""
        try:
            if market is None:
                market = self._detect_market(symbol)
            
            symbol = self.normalize_symbol(symbol, market)
            
            if market == StockMarket.A_SHARE:
                # 获取A股实时行情
                df = ak.stock_zh_a_spot_em()
                quote = df[df['代码'] == symbol]
                
                if quote.empty:
                    return None
                
                row = quote.iloc[0]
                return {
                    'symbol': symbol,
                    'name': row['名称'],
                    'current': row['最新价'],
                    'open': row['今开'],
                    'close': row['昨收'],
                    'high': row['最高'],
                    'low': row['最低'],
                    'volume': row['成交量'],
                    'amount': row['成交额'],
                    'change': row['涨跌额'],
                    'change_percent': row['涨跌幅'],
                    'turnover_rate': row.get('换手率', None),
                    'pe_ratio': row.get('市盈率-动态', None),
                    'pb_ratio': row.get('市净率', None),
                    'timestamp': datetime.now()
                }
            
            elif market == StockMarket.HONG_KONG:
                # 获取港股实时行情
                df = ak.stock_hk_spot_em()
                quote = df[df['代码'] == symbol]
                
                if quote.empty:
                    return None
                
                row = quote.iloc[0]
                return {
                    'symbol': symbol,
                    'name': row['名称'],
                    'current': row['最新价'],
                    'open': row['今开'],
                    'close': row['昨收'],
                    'high': row['最高'],
                    'low': row['最低'],
                    'volume': row['成交量'],
                    'amount': row['成交额'],
                    'change': row['涨跌额'],
                    'change_percent': row['涨跌幅'],
                    'timestamp': datetime.now()
                }
            
            elif market == StockMarket.US:
                # 获取美股实时行情
                df = ak.stock_us_spot_em()
                quote = df[df['代码'] == symbol]
                
                if quote.empty:
                    return None
                
                row = quote.iloc[0]
                return {
                    'symbol': symbol,
                    'name': row['名称'],
                    'current': row['最新价'],
                    'change': row['涨跌额'],
                    'change_percent': row['涨跌幅'],
                    'volume': row['成交量'],
                    'timestamp': datetime.now()
                }
            
            return None
            
        except Exception as e:
            self._handle_error(e, "获取股票实时行情")
            return None
    
    def get_stock_history(self, symbol: str, 
                         start_date: Union[str, date, datetime],
                         end_date: Union[str, date, datetime] = None,
                         period: DataPeriod = DataPeriod.DAILY,
                         market: StockMarket = None) -> Optional[pd.DataFrame]:
        """获取股票历史数据"""
        try:
            if market is None:
                market = self._detect_market(symbol)
            
            symbol = self.normalize_symbol(symbol, market)
            
            # 格式化日期
            if isinstance(start_date, (date, datetime)):
                start_date_str = start_date.strftime('%Y%m%d')
            else:
                start_date_str = start_date.replace('-', '')
            
            if end_date is None:
                end_date_str = datetime.now().strftime('%Y%m%d')
            elif isinstance(end_date, (date, datetime)):
                end_date_str = end_date.strftime('%Y%m%d')
            else:
                end_date_str = end_date.replace('-', '')
            
            # 映射周期
            period_mapping = {
                DataPeriod.DAILY: "daily",
                DataPeriod.WEEKLY: "weekly",
                DataPeriod.MONTHLY: "monthly"
            }
            
            ak_period = period_mapping.get(period, "daily")
            
            if market == StockMarket.A_SHARE:
                # 获取A股历史数据
                df = ak.stock_zh_a_hist(
                    symbol=symbol,
                    period=ak_period,
                    start_date=start_date_str,
                    end_date=end_date_str,
                    adjust=""
                )
                
                if df.empty:
                    return None
                
                # 标准化列名
                df = df.rename(columns={
                    '日期': 'date',
                    '开盘': 'open',
                    '收盘': 'close',
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'volume',
                    '成交额': 'amount',
                    '振幅': 'amplitude',
                    '涨跌幅': 'change_percent',
                    '涨跌额': 'change',
                    '换手率': 'turnover'
                })
                
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                
                return df
            
            elif market == StockMarket.HONG_KONG:
                # 获取港股历史数据
                df = ak.stock_hk_hist(
                    symbol=symbol,
                    period=ak_period,
                    start_date=start_date_str,
                    end_date=end_date_str,
                    adjust="qfq"
                )
                
                if df.empty:
                    return None
                
                # 标准化列名
                df = df.rename(columns={
                    '日期': 'date',
                    '开盘': 'open',
                    '收盘': 'close',
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'volume',
                    '成交额': 'amount'
                })
                
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                
                return df
            
            elif market == StockMarket.US:
                # 获取美股历史数据
                df = ak.stock_us_hist(
                    symbol=symbol,
                    period=ak_period,
                    start_date=start_date_str,
                    end_date=end_date_str,
                    adjust="qfq"
                )
                
                if df.empty:
                    return None
                
                # 标准化列名
                df = df.rename(columns={
                    '日期': 'date',
                    '开盘': 'open',
                    '收盘': 'close',
                    '最高': 'high',
                    '最低': 'low',
                    '成交量': 'volume'
                })
                
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                
                return df
            
            return None
            
        except Exception as e:
            self._handle_error(e, "获取股票历史数据")
            return None
    
    def get_company_info(self, symbol: str, market: StockMarket = None) -> Optional[Dict[str, Any]]:
        """获取公司详细信息"""
        try:
            if market is None:
                market = self._detect_market(symbol)
            
            symbol = self.normalize_symbol(symbol, market)
            
            if market == StockMarket.A_SHARE:
                # 获取A股公司信息
                try:
                    # 公司概况
                    profile_df = ak.stock_individual_info_em(symbol=symbol)
                    if profile_df.empty:
                        return None
                    
                    profile_dict = dict(zip(profile_df['item'], profile_df['value']))
                    
                    # 财务指标
                    financial_df = ak.stock_financial_em(symbol=symbol)
                    latest_financial = {}
                    if not financial_df.empty:
                        latest_row = financial_df.iloc[0]
                        latest_financial = {
                            'revenue': latest_row.get('营业收入', None),
                            'net_profit': latest_row.get('净利润', None),
                            'total_assets': latest_row.get('总资产', None),
                            'roe': latest_row.get('净资产收益率', None)
                        }
                    
                    return {
                        'symbol': symbol,
                        'name': profile_dict.get('股票简称', None),
                        'industry': profile_dict.get('所属行业', None),
                        'market_cap': profile_dict.get('总市值', None),
                        'pe_ratio': profile_dict.get('市盈率', None),
                        'pb_ratio': profile_dict.get('市净率', None),
                        'dividend_yield': profile_dict.get('股息率', None),
                        'listing_date': profile_dict.get('上市时间', None),
                        'website': profile_dict.get('公司网址', None),
                        'business_scope': profile_dict.get('经营范围', None),
                        'financial': latest_financial
                    }
                
                except Exception:
                    # 如果详细信息获取失败，尝试获取基本信息
                    basic_info = self.get_stock_info(symbol, market)
                    return basic_info
            
            return None
            
        except Exception as e:
            self._handle_error(e, "获取公司详细信息")
            return None
    
    def search_stocks(self, keyword: str, market: StockMarket = None, limit: int = 10) -> List[Dict[str, Any]]:
        """搜索股票"""
        try:
            results = []
            
            if market is None or market == StockMarket.A_SHARE:
                # 搜索A股
                df = ak.stock_zh_a_spot_em()
                mask = df['名称'].str.contains(keyword, case=False, na=False) | \
                       df['代码'].str.contains(keyword, case=False, na=False)
                
                matches = df[mask].head(limit)
                
                for _, row in matches.iterrows():
                    results.append({
                        'symbol': row['代码'],
                        'name': row['名称'],
                        'market': 'A股',
                        'current_price': row['最新价'],
                        'change_percent': row['涨跌幅']
                    })
            
            if market is None or market == StockMarket.HONG_KONG:
                # 搜索港股
                try:
                    df = ak.stock_hk_spot_em()
                    mask = df['名称'].str.contains(keyword, case=False, na=False) | \
                           df['代码'].str.contains(keyword, case=False, na=False)
                    
                    matches = df[mask].head(limit - len(results))
                    
                    for _, row in matches.iterrows():
                        results.append({
                            'symbol': row['代码'],
                            'name': row['名称'],
                            'market': '港股',
                            'current_price': row['最新价'],
                            'change_percent': row['涨跌幅']
                        })
                except Exception:
                    logger.warning("港股搜索失败")
            
            if market is None or market == StockMarket.US:
                # 搜索美股
                try:
                    df = ak.stock_us_spot_em()
                    mask = df['名称'].str.contains(keyword, case=False, na=False) | \
                           df['代码'].str.contains(keyword, case=False, na=False)
                    
                    matches = df[mask].head(limit - len(results))
                    
                    for _, row in matches.iterrows():
                        results.append({
                            'symbol': row['代码'],
                            'name': row['名称'],
                            'market': '美股',
                            'current_price': row['最新价'],
                            'change_percent': row['涨跌幅']
                        })
                except Exception:
                    logger.warning("美股搜索失败")
            
            return results[:limit]
            
        except Exception as e:
            self._handle_error(e, "搜索股票")
            return [] 