from core.Enum.TickerType import TickerType
from core.Enum.TickerKType import TickerKType

import datetime
import pandas as pd
from dateutil.relativedelta import relativedelta

from core.API import APIHelper
from core.utils import UtilsHelper

from .Ticker import Ticker
from .TickerKLine import TickerKLine
from .TickerStrategy import TickerStrategy
from .TickerIndicator import TickerIndicator
from .TickerScore import TickerScore
from .TickerFilter import TickerFilter
from .ProjectTicker import ProjectTicker
from .TickerValuation import TickerValuation

from core.API.TickerRepository import TickerRepository

class DataSourceHelper:
    tickerType = [
        TickerType.STOCK,
        TickerType.IDX,
        TickerType.ETF,
        TickerType.PLATE
    ]
    endDate = ''
    startDate = ''
    
    strategies = None
    indicators = None
    valuations = None
    scoreRule = None
    filterRulle = None

    APIHelper = APIHelper()

    def __init__(self):
        self.endDate = datetime.date.today().strftime('%Y-%m-%d')
        self.startDate = (datetime.date.today() - relativedelta(years=3)).strftime('%Y-%m-%d')

    def setEndDate(self,endDate):
        if endDate is not None:
            self.endDate = endDate
        self.startDate = (datetime.datetime.strptime(self.endDate, "%Y-%m-%d") - relativedelta(years=3)).strftime('%Y-%m-%d')

    def setStrategies(self,strategies):
        self.strategies = strategies

    def setIndicators(self,indicators):
        self.indicators = indicators

    def setScoreRule(self,scoreRule):
        self.scoreRule = scoreRule
    
    def setFilterRule(self,filterRulle):
        self.filterRulle = filterRulle

    def setValuations(self,valuations):
        self.valuations = valuations

    def getTickersQuarter(self,page):
        return APIHelper().ticker().getAllAvaiableItemsQuarter(self.endDate,page)

    ## 更新股票列表
    def updateTickerList(self):
        """
        更新股票列表
        """
        Ticker(self.endDate).update_tickers()

    # 更新个股K线
    def updateTickerKLine(self,ticker,force=False):
        return TickerKLine(ticker['code'],ticker['source'],self.startDate,self.endDate).updateTickerKLine(ticker,force)

    # 更新股票数据
    def updateTicker(self,ticker,force=False):
        # 直接从在线API获取K线数据
        kLineData = TickerKLine().get_history_kl(ticker['code'], ticker['source'], self.startDate, self.endDate)
        strategyData = TickerStrategy(self.endDate,self.strategies).updateTickerStrategy(ticker,kLineData)
        indicatorData = TickerIndicator(self.endDate,self.indicators).updateTickerIndicator(ticker,kLineData)
        valuationData = TickerValuation(self.endDate,self.valuations).updateTickerValuation(ticker)
        TickerScore(self.scoreRule).updateTickerScore(ticker,kLineData,strategyData,indicatorData,valuationData)

    # 根据code更新数据
    def updateTickerByCode(self,code,force=False):
        ticker = APIHelper().ticker().getItemByCode(code)
        if ticker is not None:
            self.updateTicker(ticker,force)
    
    # 根据code更新数据
    def updateTickerLikeCode(self,code,force=False):
        ticker = APIHelper().ticker().getItemLikeCode(code)
        if ticker is not None:
            self.updateTicker(ticker,force)

    # 更新指定股票数据
    def updateTickers(self,tickers):
        total = len(tickers)
        for i in range(total):
            ticker = tickers[i]
            UtilsHelper().runProcess(i,total,"update({i}/{total})".format(i=i+1,total=total),"({id}){code}".format(
                id = ticker['id'],
                code = ticker['code']
            ))
            self.updateTicker(ticker)

    def updateAllTicker(self):
        tickers = APIHelper().ticker().getAllAvaiableItems()
        self.updateTickers(tickers)

    # 根据更新startKey开头的数据
    def updateTickerStartWith(self,startKey):
        print('更新'+startKey+'开头的项目的数据')
        tickers = APIHelper().ticker().getAllAvaiableItemsStartWith(startKey)
        self.updateTickers(tickers)

    def updateTickerQuarter(self,page):
        print('更新分页'+page+'的项目的数据')
        tickers = APIHelper().ticker().getAllAvaiableItemsQuarter(self.endDate,page)
        self.updateTickers(tickers)

    # 分析项目数据
    def analysisTicker(self,code,days=250,kLineData=None,kScoreData=None):
        ticker = TickerRepository().get_by_code(code)
        if ticker is None:
            print("未找到目标数据")
            return

        # 统一获取和格式化日期
        current_date = datetime.datetime.now()
        endDate = current_date.strftime('%Y-%m-%d')
        startDate = (current_date - relativedelta(days=days)).strftime('%Y-%m-%d')
        
        kLineData = TickerKLine().get_history_kl(ticker.code, ticker.source, startDate, endDate)
        if kLineData:
            # 使用格式化后的字符串日期
            strategyData = TickerStrategy(endDate).update_ticker_strategy(ticker,kLineData)
            indicatorData = TickerIndicator(endDate,self.indicators).update_ticker_indicator(ticker,kLineData)
            valuationData = TickerValuation(endDate,self.valuations).update_ticker_valuation(ticker)
            TickerScore(self.scoreRule).update_ticker_score(ticker,kLineData,strategyData,indicatorData,valuationData)
        # scoreData = self.APIHelper.tickerScore().getItemsByTickerId(ticker['id']) if kScoreData is None else kScoreData

    
    # 分析即时项目数据
    def analysisTickerOnTime(self,code,days):
        ticker = self.APIHelper.ticker().getItemByCode(code)
        if not ticker:
            print("未找到目标数据")
            return
            
        # 从在线API获取K线数据和实时数据
        kLineData = TickerKLine().get_history_kl(ticker['code'], ticker['source'], self.startDate, self.endDate)
        onTimeData = TickerKLine().get_kl(ticker['code'], ticker['source'])
        
        # 确保时间是字符串格式
        time_key = self.endDate
        if onTimeData is not None:
            ontime_date = onTimeData['time_key']
            if isinstance(ontime_date, datetime.datetime):
                ontime_date = ontime_date.strftime('%Y-%m-%d')
                
            if kLineData is None:
                kLineData = [onTimeData]
            elif time_key < ontime_date:
                kLineData.append(onTimeData)
            elif time_key == ontime_date:
                kLineData[len(kLineData) - 1] = onTimeData
                
        strategyData = TickerStrategy(time_key).calculate(kLineData)
        indicatorData = TickerIndicator(time_key).calculate(kLineData)
        scoreData = TickerScore(self.scoreRule).calculate(ticker,kLineData,strategyData,indicatorData,None)
        # TickerAnalysis(days).run(ticker,kLineData,scoreData)
    
    # def getRecommendProjectTickers(self,startKey = None):
    #     tickers = pd.read_csv('output/recommendProject.csv')
    #     result = []
    #     for i in range(len(tickers)):
    #         code = tickers['code'][i]
    #         if startKey is None or code.startswith(startKey):
    #             result.append(code)
    #     return result

    def isRecommendTicker(self,code):
        ticker = self.APIHelper.ticker().getItemByCode(code)
        TickerFilter(self.filterRulle).run([ticker])
    
    # 推荐项目
    def updateRecommendProjectTicker(self,avaiableTickers):
        tickers = TickerFilter(self.filterRulle).run(avaiableTickers)
        if len(tickers) > 0:
            watchList =  pd.DataFrame(tickers)
            watchList.set_index(['code'], inplace=True)
            watchList.to_csv('output/recommend.csv',index=True,header=True)

    # 更新可推荐项目
    def updateRecommendTickers(self):
        avaiableTickers = self.APIHelper.ticker().getAllAvaiableItems(self.endDate)
        self.updateRecommendProjectTicker(avaiableTickers)
        
    # 获取可推荐项目
    def getRecommendTickers(self,startKey = None):
        tickers = pd.read_csv('output/recommend.csv')
        result = []
        for i in range(len(tickers)):
            code = tickers['code'][i]
            if (startKey is None or code.startswith(startKey)):
                result.append(code)
        return result
