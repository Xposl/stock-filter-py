import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
import numpy as np
import mplcursors

from core.API import APIHelper

from core.utils import UtilsHelper

class TickerAnalysis:
    source = []
    days = 300

    def __init__(self,days = None):
        if days is not None:
            self.days = days

    def run(self,ticker,kLineData,scoreData):
        if ticker is None or ticker['is_deleted'] == 1 or ticker['status'] == 0:
            raise Exception('项目已经删除或不生效[{id}]{code}'.format(id=ticker['id'],code=ticker['code']))

        length = len(kLineData)
        start = length - self.days if length - self.days > 0 else 0

        valuation = APIHelper().tickerValuation().getItemByTickerIdAndKey(ticker['id'],'Research_Report_Valuation')
        targetPrice = valuation['target_price'] if valuation is not None else None

        kLine = pd.DataFrame(kLineData)
        kLine['dates'] = pd.to_datetime(kLine['time_key'])
        kLine['index'] = np.arange(0,len(kLine))
        kLine.set_index(['dates'], inplace=True)
        kFullScore = pd.DataFrame(scoreData)
        score = kFullScore['score'].values
        maScore = UtilsHelper().WMA(kFullScore['score'].values,7)
        maScoreL = UtilsHelper().WMA(kFullScore['score'].values,21)

        kLine.head()
        fig, (ax1, ax2) = plt.subplots(2, sharex=True, figsize=(15,6))

        mpf.plot(kLine,
            ax=ax1,
            mav=(13,21,144, 169, 288, 338),
            type = 'candle',
            style='binance',
            warn_too_much_data=900,
            datetime_format='%Y-%m-%d',
            show_nontrading=False
        )
        ax1.grid(True)
        
        lines = plt.plot(kLine['index'],score,"o:",color = 'black')
        plt.plot(kLine['index'],maScore,color = 'red')
        plt.plot(kLine['index'],maScoreL,color = 'blue')
        
        plt.fill_between(kLine['index'],0,30, facecolor='red',alpha=0.3)
        plt.fill_between(kLine['index'],70,100, facecolor='green',alpha=0.3)
        plt.axis([kLine['index'][start],kLine['index'][len(kLine)-1]+1,0,100])
        ax2.grid(True)

        plt.title('[{id}]({code}){name}:({price})({score})-target:{targetPrice}'.format(
            id = str(ticker['id']),
            code = ticker['code'],
            name = ticker['name'],
            price = kLine['close'][length-1],
            score = kFullScore['score'][length - 1],
            targetPrice = targetPrice
        ))
        plt.xticks(rotation=30)
        plt.tight_layout()
        

        cursor = mplcursors.cursor(lines)
        @cursor.connect("add")
        def on_add(sel):
            sel.annotation.set_text(kLine['close'][int(sel.index)])
        plt.show()

