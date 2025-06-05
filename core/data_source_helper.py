import time
from typing import List, Optional
import akshare as ak
from core.enum.ticker_type import TickerType

import datetime
from dateutil.relativedelta import relativedelta

from core.handler.ticker_analysis_handler import TickerAnalysisHandler
from core.handler.ticker_k_line_handler import TickerKLineHandler
from core.models.ticker import Ticker
from core.models.ticker_score import TickerScore
from core.schema.k_line import KLine
from core.service.ticker_score_repository import TickerScoreRepository
from core.utils.utils import UtilsHelper

from .handler.ticker_handler import TickerHandler

from .handler.ticker_strategy_handler import TickerStrategyHandler
from .handler.ticker_indicator_handler import TickerIndicatorHandler
from .handler.ticker_score_handler import TickerScoreHandler
from .handler.ticker_valuation_handler import TickerValuationHandler

from core.service.ticker_repository import TickerRepository

class DataSourceHelper:
    tickerType = [
        TickerType.STOCK,
        TickerType.IDX,
        TickerType.ETF,
        TickerType.PLATE
    ]
    
    strategies = None
    indicators = None
    valuations = None
    scoreRule = None
    filterRulle = None

    def set_strategies(self,strategies: Optional[list]=None):
        """
        设置策略
        """
        self.strategies = strategies

    def set_indicators(self,indicators: Optional[list]=None):
        """
        设置指标
        """
        self.indicators = indicators

    def set_score_rule(self,scoreRule: Optional[list]=None):
        """
        设置评分规则
        """
        self.scoreRule = scoreRule
    
    def set_filter_rule(self,filterRulle: Optional[list]=None):
        """
        设置过滤规则
        """
        self.filterRulle = filterRulle

    def set_valuations(self,valuations: Optional[list]=None):
        """
        设置估值规则
        """
        self.valuations = valuations

    def _get_end_date(self) -> str:
        """
        获取最后交易日
        """
        # A股最后交易日
        try:
            stock_sse_summary_df = ak.stock_sse_summary()
            report_time_row = stock_sse_summary_df[stock_sse_summary_df.iloc[:, 0] == "报告时间"]
            if not report_time_row.empty:
                # 获取"股票"列的值（第2列，索引为1）
                report_time_str = report_time_row.iloc[0, 1]
                # 格式化日期字符串
                return f"{report_time_str[:4]}-{report_time_str[4:6]}-{report_time_str[6:]}"
        except Exception as e:
            print("获取失败")
            return datetime.datetime.now().strftime('%Y-%m-%d')
        
    def _calc_start_end_date(self,days: Optional[int]=600) -> tuple[str,str]:
        """
        计算开始和结束日期
        :param days: 天数
        :return: 开始和结束日期
        """
        end_date = self._get_end_date()
        start_date = (datetime.datetime.strptime(end_date, '%Y-%m-%d') - relativedelta(days=days)).strftime('%Y-%m-%d')
        return start_date, end_date

    
    def _get_on_time_kline_data(self,ticker: Ticker, days: Optional[int]=600):
        """
        获取指定股票的K线数据
        """
        # 从在线API获取K线数据和实时数据
        current_date = datetime.datetime.now()
        end_date = current_date.strftime('%Y-%m-%d')
        start_date = (current_date - relativedelta(days=days)).strftime('%Y-%m-%d')
        
        kLineData, used_source = TickerKLineHandler().get_kl(ticker.code, ticker.source, start_date, end_date)
        onTimeData, used_source_on_time = TickerKLineHandler().get_kl_on_time(ticker.code, ticker.source)
        # 同步source字段
        if used_source is not None and used_source != ticker.source and kLineData is not None and len(kLineData) > 0:
            TickerRepository().update(ticker.code, ticker.name, {"source": used_source})
            ticker.source = used_source
        # 确保时间是字符串格式
        time_key = end_date
        if onTimeData is not None:
            ontime_date = onTimeData['time_key'] if isinstance(onTimeData, dict) else getattr(onTimeData, 'time_key', None)
            if isinstance(ontime_date, (datetime.datetime, datetime.date)):
                ontime_date = ontime_date.strftime('%Y-%m-%d')
            if kLineData is None:
                kLineData = [onTimeData]
            elif time_key < ontime_date:
                kLineData.append(onTimeData)
            elif time_key == ontime_date:
                kLineData[len(kLineData) - 1] = onTimeData
        return time_key, kLineData

    def _update_ticker_data(self,ticker: Ticker, end_date: str, kl_data: List[KLine]):
        """
        更新指定股票的分析数据
        """
        if kl_data:
            # 使用格式化后的字符串日期
            strategyData = TickerStrategyHandler().update_ticker_strategy(ticker,kl_data, end_date)
            indicatorData = TickerIndicatorHandler(end_date,self.indicators).update_ticker_indicator(ticker,kl_data)
            valuationData = TickerValuationHandler(end_date,self.valuations).update_ticker_valuation(ticker)
            scoreData = TickerScoreHandler(self.scoreRule).update_ticker_score(ticker,kl_data,strategyData,indicatorData,valuationData)
        return ticker,kl_data,scoreData

    def _update_ticker(self,ticker: Ticker,days: Optional[int]=600, source: Optional[int]=None):
        """
        更新指定股票数据
        """
        from core.service.ticker_repository import TickerRepository
        # 统一获取和格式化日期
        start_date, end_date = self._calc_start_end_date(days)
        kl_data, used_source = TickerKLineHandler().get_kl(ticker.code, source if source != None else ticker.source, start_date, end_date)
        # 同步source字段
        if used_source is not None and used_source != ticker.source and kl_data is not None and len(kl_data) > 0:
            TickerRepository().update(ticker.code, ticker.name, {"source": used_source})
            ticker.source = used_source
        return self._update_ticker_data(ticker, end_date, kl_data)


    def _update_tickers(self,tickers: Optional[list]=None,days: Optional[int]=600):
        """
        更新指定股票数据
        """
        total = len(tickers)
        end_date = self._get_end_date()
        for i in range(total):
            ticker = tickers[i]
            UtilsHelper().run_process(i,total,"update({i}/{total})".format(i=i+1,total=total),"({id}){code}".format(
                id = ticker.id,
                code = ticker.code
            ))
            kScore = TickerScoreRepository().get_items_by_ticker_id(ticker.id)

            if kScore != None and len(kScore) > 0 and kScore[0].time_key == end_date:
                continue
            try:
                self._update_ticker(ticker, days, i % 2 + 1)
            except Exception as e:
                print("更新数据失败[{id}]{code} {error}".format(id=ticker.id,code=ticker.code,error=str(e)))
            time.sleep(1)

    def get_ticker_code(self, market: str, ticker_code: str) -> str:
        """
        将原始股票代码转换为系统标准格式（包含市场前缀）
        
        Args:
            market: 市场标识
                - "zh": 中国A股市场
                - "hk": 香港股市
                - "us": 美国股市
            ticker_code: 原始股票代码（不含前缀）
                - A股：如 "600000", "000001"
                - 港股：如 "700", "00700"  
                - 美股：如 "AAPL", "TSLA"
                
        Returns:
            str: 标准格式的股票代码
                - A股：SH.600000 或 SZ.000001 (自动判断交易所)
                - 港股：HK.00700 (自动补零到5位)
                - 美股：US.AAPL
                
        Example:
            get_ticker_code("zh", "600000")  # 返回 "SH.600000"
            get_ticker_code("zh", "000001")  # 返回 "SZ.000001"
            get_ticker_code("hk", "700")     # 返回 "HK.00700"
            get_ticker_code("us", "AAPL")    # 返回 "US.AAPL"
        """
        code = None
        if market == "hk":
            code = f"HK.{ticker_code.zfill(5)}"
        elif market == "zh":
            code = ticker_code.zfill(6)
            if code.startswith('0') or code.startswith('3'):
                code = f"SZ.{code}"
            elif code.startswith('6') or code.startswith('7') or code.startswith('9'):
                code = f"SH.{code}"
        elif market == "us":
            code = f"US.{ticker_code}"
        
        return code

    def update_ticker_list(self):
        """
        更新股票列表
        """
        TickerHandler().update_tickers()

    def get_kline_data(self,code: str,days: Optional[int]=600):
        """
        获取指定股票的K线数据
        """
        ticker = TickerRepository().get_by_code(code)
        if ticker is None:
            print("未找到目标数据")
            return
        # 统一获取和格式化日期
        start_date, end_date = self._calc_start_end_date(days)
        kLineData = TickerKLineHandler().get_kl(ticker.code, ticker.source, start_date, end_date)
        return kLineData
    
    def update_all_tickers(self):
        """
        更新所有股票数据
        """
        tickers = TickerRepository().get_all_available()
        self._update_tickers(tickers)

    def update_tickers_start_with(self,startKey):
        """
        更新startKey开头的数据
        """
        print('更新'+startKey+'开头的项目的数据')
        tickers = TickerRepository().get_all_available_start_with(startKey)
        self._update_tickers(tickers)

    def get_ticker_data(self, code: str, days: Optional[int]=600) -> tuple[Ticker,List[KLine],List[TickerScore]]:
        """
        获取指定股票数据
        
        Args:
            code: 股票代码，必须包含市场前缀，格式如下：
                - A股：SH.600000 (上交所) 或 SZ.000001 (深交所)
                - 港股：HK.00700 (5位数字，不足5位前面补0)
                - 美股：US.AAPL 
                注意：不支持纯数字代码，必须包含市场前缀
            days: 获取的历史数据天数，默认600天
            
        Returns:
            tuple[Ticker, List[KLine], List[TickerScore]]: 
                - Ticker: 股票基础信息，如果股票不存在则返回None
                - List[KLine]: K线数据列表
                - List[TickerScore]: 评分数据列表
                
        Example:
            ticker, kl_data, score_data = helper.get_ticker_data("SH.600000", 250)
            ticker, kl_data, score_data = helper.get_ticker_data("HK.00700", 180)
            ticker, kl_data, score_data = helper.get_ticker_data("US.AAPL", 365)
        """
        ticker = TickerRepository().get_by_code(code)
        ticker,kl_data,scoreData =  self._update_ticker(ticker,days)
        return ticker,kl_data,scoreData
    
    def get_ticker_data_on_time(self, code: str,days: Optional[int]=600) -> Optional[tuple]:
        """
        获取即时项目数据
        """
        ticker = TickerRepository().get_by_code(code)
        if ticker is None:
            print("未找到目标数据")
            return
            
        # 从在线API获取K线数据和实时数据
        time_key, kLineData = self._get_on_time_kline_data(ticker,days)     
        strategyData = TickerStrategyHandler(time_key).calculate(kLineData)
        indicatorData = TickerIndicatorHandler(time_key).calculate(kLineData)
        scoreData = TickerScoreHandler(self.scoreRule).calculate(ticker,kLineData,strategyData,indicatorData,None)
        return ticker,kLineData,scoreData

    def analysis_ticker(self,code: str,days: Optional[int]=600):
        """
        分析项目数据
        """
        ticker = TickerRepository().get_by_code(code)
        if ticker is None:
            print("未找到目标数据")
            return
        
        ticker,kLineData,scoreData = self._update_ticker(ticker,days)
        TickerAnalysisHandler().run(ticker,kLineData,scoreData)

    
    def analysis_ticker_on_time(self,code: str,days: Optional[int]=600,kLineData=None): 
        """
        分析即时项目数据
        """
        ticker,kLineData,scoreData = self.get_ticker_data_on_time(code,days,kLineData)
        TickerAnalysisHandler().run(ticker,kLineData,scoreData)

    

