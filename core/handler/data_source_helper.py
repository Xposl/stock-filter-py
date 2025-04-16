import time
import akshare as ak
from core.enum.ticker_type import TickerType

import datetime
from dateutil.relativedelta import relativedelta

from core.handler.ticker_analysis_handler import TickerAnalysisHandler
from core.service.ticker_score_repository import TickerScoreRepository
from core.utils import UtilsHelper

from .ticker_handler import TickerHandler
from .ticker_k_line_handler import TickerKLineHandler
from .ticker_strategy_handler import TickerStrategyHandler
from .ticker_indicator_handler import TickerIndicatorHandler
from .ticker_score_handler import TickerScoreHandler
from .ticker_valuation_handler import TickerValuationHandler

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

    def set_strategies(self,strategies):
        self.strategies = strategies

    def set_indicators(self,indicators):
        self.indicators = indicators

    def set_score_rule(self,scoreRule):
        self.scoreRule = scoreRule
    
    def set_filter_rule(self,filterRulle):
        self.filterRulle = filterRulle

    def set_valuations(self,valuations):
        self.valuations = valuations

    def _get_end_date(self):
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
            return datetime.datetime.now()
        
    def _calc_start_end_date(self,days=600):
        """
        计算开始和结束日期
        :param days: 天数
        :return: 开始和结束日期
        """
        endDate = self._get_end_date()
        startDate = (datetime.datetime.strptime(endDate, '%Y-%m-%d') - relativedelta(days=days)).strftime('%Y-%m-%d')
        return startDate, endDate


    ## 更新股票列表
    def update_ticker_list(self):
        """
        更新股票列表
        """
        TickerHandler().update_tickers()

    def get_kline_data(self,code,days=600):
        """
        获取指定股票的K线数据
        """
        ticker = TickerRepository().get_by_code(code)
        if ticker is None:
            print("未找到目标数据")
            return
        # 统一获取和格式化日期
        startDate, endDate = self._calc_start_end_date(days)
        kLineData = TickerKLineHandler().get_history_kl(ticker.code, ticker.source, startDate, endDate)
        return kLineData

    # 分析项目数据
    def update_ticker(self,ticker,days=600, source=None):
        # 统一获取和格式化日期
        startDate, endDate = self._calc_start_end_date(days)
        kLineData = TickerKLineHandler().get_history_kl(ticker.code, source if source != None else ticker.source, startDate, endDate)
        if kLineData:
            # 使用格式化后的字符串日期
            strategyData = TickerStrategyHandler().update_ticker_strategy(ticker,kLineData, endDate)
            indicatorData = TickerIndicatorHandler(endDate,self.indicators).update_ticker_indicator(ticker,kLineData)
            valuationData = TickerValuationHandler(endDate,self.valuations).update_ticker_valuation(ticker)
            scoreData = TickerScoreHandler(self.scoreRule).update_ticker_score(ticker,kLineData,strategyData,indicatorData,valuationData)
        return ticker,kLineData,scoreData


    # 更新指定股票数据
    def update_tickers(self,tickers,days=600):
        total = len(tickers)
        end_date = self._get_end_date()
        for i in range(total):
            ticker = tickers[i]
            UtilsHelper().runProcess(i,total,"update({i}/{total})".format(i=i+1,total=total),"({id}){code}".format(
                id = ticker.id,
                code = ticker.code
            ))
            kScore = TickerScoreRepository().get_items_by_ticker_id(ticker.id)

            if kScore != None and len(kScore) > 0 and kScore[0].time_key == end_date:
                continue
            try:
                self.update_ticker(ticker, days, i % 2 + 1)
            except Exception as e:
                print("更新数据失败[{id}]{code} {error}".format(id=ticker.id,code=ticker.code,error=str(e)))
            time.sleep(1)

    def update_all_tickers(self):
        tickers = TickerRepository().get_all_available()
        self.update_tickers(tickers)

    # 根据更新startKey开头的数据
    def update_tickers_start_with(self,startKey):
        print('更新'+startKey+'开头的项目的数据')
        tickers = TickerRepository().get_all_available_start_with(startKey)
        self.update_tickers(tickers)


    # 分析项目数据
    def analysis_ticker(self,code,days=250):
        ticker = TickerRepository().get_by_code(code)
        if ticker is None:
            print("未找到目标数据")
            return
        
        ticker,kLineData,scoreData = self.update_ticker(ticker,days)
        TickerAnalysisHandler().run(ticker,kLineData,scoreData)

    # 分析即时项目数据
    def analysis_ticker_on_time(self,code,days=250,kLineData=None):
        ticker = TickerRepository().get_by_code(code)
        if ticker is None:
            print("未找到目标数据")
            return
            
        # 从在线API获取K线数据和实时数据
        current_date = datetime.datetime.now()
        endDate = current_date.strftime('%Y-%m-%d')
        startDate = (current_date - relativedelta(days=days)).strftime('%Y-%m-%d')
        
        kLineData = TickerKLineHandler().get_history_kl(ticker.code, ticker.source, startDate, endDate)
        onTimeData = TickerKLineHandler().get_kl(ticker.code, ticker.source)
        
        # 确保时间是字符串格式
        time_key = endDate
        if onTimeData is not None:
            ontime_date = onTimeData['time_key']
            if isinstance(ontime_date, (datetime.datetime, datetime.date)):
                ontime_date = ontime_date.strftime('%Y-%m-%d')
                
            if kLineData is None:
                kLineData = [onTimeData]
            elif time_key < ontime_date:
                kLineData.append(onTimeData)
            elif time_key == ontime_date:
                kLineData[len(kLineData) - 1] = onTimeData
                
        strategyData = TickerStrategyHandler(time_key).calculate(kLineData)
        indicatorData = TickerIndicatorHandler(time_key).calculate(kLineData)
        scoreData = TickerScoreHandler(self.scoreRule).calculate(ticker,kLineData,strategyData,indicatorData,None)
        TickerAnalysisHandler().run(ticker,kLineData,scoreData)
    

