import akshare as ak
import datetime
import math

from core.Enum.TickerType import TickerType
from core.API import APIHelper
from core.API.Helper.XueqiuHelper import Xueqiu

class dongcaiSource:
    def __init__(self, code, startDate=None, endDate=None):
        self.code = code
        self.startDate = startDate
        self.endDate = endDate

    def get_data_time_key(self, data, index):
        return data['日期'][index]

    def convert_data(self, data, index):
        return {
            'time_key': data['日期'][index],
            'high': data['最高'][index],
            'low': data['最低'][index],
            'open': data['开盘'][index],
            'close': data['收盘'][index],
            'volume': data['成交量'][index],
            'turnover': data['成交额'][index],
            'turnover_rate': data['换手率'][index]
        }

    def convert_on_time_data(self, data, index):
        return {
            'time_key': datetime.date.today(),
            'high': data['最高'][index],
            'low': data['最低'][index],
            'open': data['今开'][index],
            'close': data['最新价'][index],
            'volume': data['成交量'][index],
            'turnover': data['成交额'][index],
            'turnover_rate': 0
        }

    def convert_us_on_time_data(self, data, index):
        return {
            'time_key': datetime.date.today(),
            'high': data['最高价'][index],
            'low': data['最低价'][index],
            'open': data['开盘价'][index],
            'close': data['最新价'][index],
            'volume': 0,
            'turnover': 0,
            'turnover_rate': 0
        }

    def get_zh_on_time_data(self):
        tickers = ak.stock_zh_a_spot_em()
        for i in range(len(tickers)):
            code = tickers['代码'][i]
            if code.startswith('0') or code.startswith('3'):
                code = 'SZ.%s' % str(code)
            elif code.startswith('6') or code.startswith('7') or code.startswith('9'):
                code = 'SH.%s' % str(code)
            if code == self.code:
                return self.convert_on_time_data(tickers, i)
        return None

    def get_hk_on_time_data(self):
        tickers = ak.stock_hk_spot_em()
        for i in range(len(tickers)):
            code = 'HK.%s' % tickers['代码'][i]
            if code == self.code:
                return self.convert_on_time_data(tickers, i)
        return None

    def get_us_on_time_data(self):
        tickers = ak.stock_us_spot_em()
        for i in range(len(tickers)):
            code = 'US.%s' % tickers['代码'][i][4:]
            if code == self.code:
                return self.convert_us_on_time_data(tickers, i)
        return None

    def get_on_time_kl(self):
        data = None
        if self.code.startswith('US'):
            data = self.get_us_on_time_data()
        elif self.code.startswith('HK'):
            data = self.get_hk_on_time_data()
        elif self.code.startswith('SZ') or self.code.startswith('SH'):
            data = self.get_zh_on_time_data()
        if data is not None:
            data['id'] = 0
        return data

    def get_kl(self):
        # 如果没有提供日期范围，直接返回实时数据
        if self.startDate is None or self.endDate is None:
            return self.get_on_time_kl()
            
        data = None
        startDate = datetime.datetime.strptime(self.startDate, "%Y-%m-%d").strftime('%Y%m%d')
        endDate = datetime.datetime.strptime(self.endDate, "%Y-%m-%d").strftime('%Y%m%d')
        if self.code.startswith('US'):
            data = ak.stock_us_hist(symbol='105.'+self.code[3:], start_date=startDate, end_date=endDate, adjust="qfq")
        elif self.code.startswith('HK'):
            data = ak.stock_hk_hist(symbol=self.code[3:], start_date=startDate, end_date=endDate, adjust="qfq")
        elif self.code.startswith('SZ') or self.code.startswith('SH'):
            data = ak.stock_zh_a_hist(symbol=self.code[3:], start_date=startDate, end_date=endDate, adjust="qfq")
        return data

class sinaSource: 
    def __init__(self, code, startDate=None, endDate=None):
        self.code = code
        self.startDate = startDate
        self.endDate = endDate
        self.type = 0

    def get_data_time_key(self, data, index):
        if self.type == 1:
            return data.index[index].strftime('%Y-%m-%d')
        return data['date'][index] if type(data['date'][index]) == str else data['date'][index].strftime('%Y-%m-%d')

    def convert_data(self, data, index):
        return {
            'time_key': self.get_data_time_key(data, index),
            'high': data['high'][index],
            'low': data['low'][index],
            'open': data['open'][index],
            'close': data['close'][index],
            'volume': data['volume'][index],
            'turnover': data['volume'][index] * data['low'][index],
            'turnover_rate': 0
        }

    def convert_on_time_data(self, data):
        # 根据实时数据API的返回结构进行转换
        if data is None:
            return None

        return {
            'time_key': datetime.date.today(),
            'high': data.get('high', 0),
            'low': data.get('low', 0),
            'open': data.get('open', 0),
            'close': data.get('price', 0), # 假设返回的实时价格字段名为'price'
            'volume': data.get('volume', 0),
            'turnover': data.get('amount', 0),
            'turnover_rate': 0,
            'id': 0
        }

    def get_on_time_kl(self):
        # 获取实时数据
        try:
            symbol = ""
            if self.code.startswith('US'):
                symbol = "gb_" + self.code[3:].lower()
            elif self.code.startswith('HK'):
                symbol = "hk" + self.code[3:]
            elif self.code.startswith('SZ'):
                symbol = "sz" + self.code[3:]
            elif self.code.startswith('SH'):
                symbol = "sh" + self.code[3:]
            else:
                return None
                
            # 使用akshare提供的实时行情API，根据symbol规则获取数据
            # 这里假设ak中有一个stock_quote_sina函数可以获取新浪实时行情
            # 实际使用时请检查akshare的API文档
            try:
                # 尝试使用stock_zh_a_spot_em获取A股实时数据
                if self.code.startswith('SZ') or self.code.startswith('SH'):
                    tickers = ak.stock_zh_a_spot_em()
                    for i in range(len(tickers)):
                        code = tickers['代码'][i]
                        if (self.code.startswith('SZ') and code.startswith('0') or code.startswith('3')) or \
                           (self.code.startswith('SH') and (code.startswith('6') or code.startswith('7') or code.startswith('9'))):
                            if self.code.endswith(code):
                                return {
                                    'time_key': datetime.date.today(),
                                    'high': tickers['最高'][i],
                                    'low': tickers['最低'][i],
                                    'open': tickers['今开'][i],
                                    'close': tickers['最新价'][i],
                                    'volume': tickers['成交量'][i],
                                    'turnover': tickers['成交额'][i],
                                    'turnover_rate': 0,
                                    'id': 0
                                }
                return None
            except Exception as e:
                print(f"获取新浪实时数据失败: {e}")
                return None
        except Exception as e:
            print(f"获取新浪实时数据失败: {e}")
            return None

    def get_kline_data(self):
        # 如果没有提供日期范围，直接返回实时数据
        if self.startDate is None or self.endDate is None:
            return None
            
        data = None
        if self.code.startswith('US'):
            data = ak.stock_us_daily(symbol=self.code[3:], adjust="qfq")
            self.type = 1
        elif self.code.startswith('HK'):
            data = ak.stock_hk_daily(symbol=self.code[3:], adjust="qfq")
        elif self.code.startswith('SZ'):
            data = ak.stock_zh_a_daily(symbol='sz'+self.code[3:], end_date=self.endDate, adjust="qfq")
        elif self.code.startswith('SH'):
            data = ak.stock_zh_a_daily(symbol='sh'+self.code[3:], end_date=self.endDate, adjust="qfq")
        return data

    def get_kl(self):
        # 优先尝试获取实时数据
        if self.startDate is None or self.endDate is None:
            return self.get_on_time_kl()
        return self.get_kline_data()

class xueqiuSource:
    def __init__(self, code, startDate=None, endDate=None):
        self.code = code
        self.startDate = startDate
        self.endDate = endDate

    def get_data_time_key(self, data, index):
        return datetime.datetime.fromtimestamp(data['日期'][index]/1000).strftime('%Y-%m-%d')

    def convert_data(self, data, index):
        return {
            'time_key': self.get_data_time_key(data, index),
            'high': data['最高'][index],
            'low': data['最低'][index],
            'open': data['开盘'][index],
            'close': data['收盘'][index],
            'volume': data['成交量'][index],
            'turnover': 0 if math.isnan(data['成交额'][index]) else data['成交额'][index],
            'turnover_rate': 0 if math.isnan(data['换手率'][index]) else data['换手率'][index]
        }

    def get_kline_data(self):
        # 如果没有提供日期范围，使用今天作为开始日期
        start_date = self.startDate if self.startDate else datetime.date.today().strftime('%Y-%m-%d')
        
        if self.code.startswith('US') or self.code.startswith('HK'):
            data = Xueqiu().getStockHistory(self.code[3:], start_date)
        elif self.code.startswith('SZ'):
            data = Xueqiu().getStockHistory('SZ'+self.code[3:], start_date)
        elif self.code.startswith('SH'):
            data = Xueqiu().getStockHistory('SH'+self.code[3:], start_date)
        return data

    def get_on_time_kl(self):
        try:
            # 尝试从雪球获取实时行情数据
            stock_code = ""
            if self.code.startswith('US') or self.code.startswith('HK'):
                stock_code = self.code[3:]
            elif self.code.startswith('SZ'):
                stock_code = 'SZ' + self.code[3:]
            elif self.code.startswith('SH'):
                stock_code = 'SH' + self.code[3:]
                
            quote = Xueqiu().getStockQuote(stock_code)
            if quote:
                return {
                    'time_key': datetime.date.today(),
                    'high': quote.get('high', 0),
                    'low': quote.get('low', 0),
                    'open': quote.get('open', 0),
                    'close': quote.get('current', 0),
                    'volume': quote.get('volume', 0),
                    'turnover': quote.get('amount', 0),
                    'turnover_rate': quote.get('turnover_rate', 0) if 'turnover_rate' in quote else 0,
                    'id': 0
                }
            return None
        except Exception as e:
            print(f"获取雪球实时数据失败: {e}")
            return None
            
    def get_kl(self):
        # 优先尝试获取实时数据
        real_time_data = self.get_on_time_kl()
        if real_time_data:
            return real_time_data
            
        # 如果实时数据获取失败且有日期范围，尝试获取历史数据
        if self.startDate:
            return self.get_kline_data()
        return None

class TickerKLine:
    """
    股票K线数据工具类
    支持从不同数据源获取股票K线数据
    """
    tickerType = [
        TickerType.STOCK,
        TickerType.IDX,
        TickerType.ETF,
        TickerType.PLATE
    ]

    def __init__(self):
        """
        初始化TickerKLine工具类
        现在改为工具类形式，不需要初始化参数
        """
        pass
    
    def get_history_kl(self, code, source, startDate=None, endDate=None):
        """
        获取历史K线数据
        
        参数:
            code: 股票代码 (必填)
            source: 数据源 1=东财 2=新浪 3=雪球 (必填)
            startDate: 开始日期，格式为'YYYY-MM-DD'
            endDate: 结束日期，格式为'YYYY-MM-DD'
            
        返回:
            K线数据列表
        """
        if not startDate or not endDate:
            print('获取历史数据需要提供开始和结束日期')
            return None
        
        # 根据参数创建数据源
        if source == 1:
            data_source = dongcaiSource(code, startDate, endDate)
        elif source == 2:
            data_source = sinaSource(code, startDate, endDate)
        elif source == 3:
            data_source = xueqiuSource(code, startDate, endDate)
        else:
            print(f"未知数据源: {source}")
            return None
 
        # 获取K线数据
        result = []
        data = data_source.get_kl()
        if data is None:
            print(f'数据失效 source:{source}')
            return None
        
        # 如果返回的是实时数据（一个dict而不是dataframe）
        if isinstance(data, dict):
            return [data]
        
        # 处理历史数据
        for i in range(len(data)):
            time_key = data_source.get_data_time_key(data, i)
            # 确保类型一致，将time_key作为字符串与字符串日期比较
            if isinstance(time_key, datetime.date):
                time_key_str = time_key.strftime('%Y-%m-%d')
            else:
                time_key_str = str(time_key)
                
            if time_key_str >= startDate and time_key_str <= endDate:
                result.append(data_source.convert_data(data, i))
        return result

    def get_kl(self, code, source):
        """
        获取最新K线数据
        
        参数:
            code: 股票代码 (必填)
            source: 数据源 1=东财 2=新浪 3=雪球 (必填)
            
        返回:
            最新的K线数据
        """
        try:
            # 根据参数创建数据源
            if source == 1:
                data_source = dongcaiSource(code)
            elif source == 2:
                data_source = sinaSource(code)
            elif source == 3:
                data_source = xueqiuSource(code)
            else:
                print(f"未知数据源: {source}")
                return None
            
            # 获取实时数据
            data = data_source.get_kl()
            
            # 如果是字典类型的数据（单条数据），直接返回
            if isinstance(data, dict):
                return data
                
            # 如果是DataFrame类型的数据，获取最后一条
            if data is not None and len(data) > 0:
                if hasattr(data_source, 'convert_data'):
                    return data_source.convert_data(data, len(data) - 1)
                    
            # 数据获取失败，尝试使用东财数据源作为备选
            if source != 1:
                return dongcaiSource(code).get_on_time_kl()
                
            return None
        except Exception as e:
            print(f"获取实时K线数据失败: {e}")
            # 出错时尝试使用东财数据源作为备选
            if source != 1:
                try:
                    return dongcaiSource(code).get_on_time_kl()
                except:
                    pass
            return None
