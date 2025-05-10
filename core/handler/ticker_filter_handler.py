
from typing import Optional
from .ticker_k_line_handler import TickerKLineHandler

from core.enum.ticker_k_type import TickerKType
from core.filter import Filter
from core.utils.utils import UtilsHelper
import datetime
from dateutil.relativedelta import relativedelta

class TickerFilterHandler:
    rule = None

    def __init__(self,rule: Optional[list]=None):
        """
        初始化
        """
        if rule is not None:
            self.rule = rule
        self.endDate = datetime.date.today().strftime('%Y-%m-%d')
        self.startDate = (datetime.date.today() - relativedelta(years=3)).strftime('%Y-%m-%d')

    def run(self,tickers: Optional[list]=None):
        """
        运行
        """
        result = []
        total = len(tickers)
        for i in range(total):
            ticker = tickers[i]
            UtilsHelper().run_process(i,total,"recommend","[total:{total}]({id}){code}".format(
                id = ticker['id'],
                code = ticker['code'],
                total = len(result)
            ))
            
            # 使用TickerKLine从在线API获取K线数据
            ticker_kline = TickerKLineHandler()
            kLineData = ticker_kline.get_history_kl(ticker['code'], ticker['source'], self.startDate, self.endDate)
            strategyData = self.APIHelper.tickerStrategy().getItemsByTickerId(ticker['id'],TickerKType.DAY.value)
            indicatorData = self.APIHelper.tickerIndicator().getItemsByTickerId(ticker['id'],TickerKType.DAY.value)
            scoreData = self.APIHelper.tickerScore().getItemsByTickerId(ticker['id'])
            valuationData = self.APIHelper.tickerValuation().getItemsByTickerId(ticker['id'])
            filter = Filter(self.rule).calculate(ticker,kLineData,strategyData,indicatorData,scoreData,valuationData)
            if filter:
                print(ticker['code'] + ":"+ticker['name']+"\n")
                result.append(ticker)
        return result
