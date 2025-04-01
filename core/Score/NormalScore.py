import json

from core.API import APIHelper
from core.Indicator import Indicator as Helper
from core.Enum.IndicatorGroup import IndicatorGroup

class NormalScore:

    def calculate(self,ticker,kLineData,strategyData,indicatorData,valuationData):
        tickerId = ticker['id']
        length = len(kLineData)
        if length == 0:
            print('无数据')
            return
        
        result = []
        maTotal = 0
        inTotal = 0
        strategyTotal = len(strategyData)
        for i in range(length):
            result.append({
                'id': kLineData[i]['id'],
                'time_key': kLineData[i]['time_key'],
                'ticker_id': tickerId,
                'ma_buy': 0,
                'ma_sell': 0,
                'ma_score': 0,
                'in_buy': 0,
                'in_sell': 0,
                'in_score': 0,
                'strategy_buy': 0,
                'strategy_sell': 0,
                'strategy_score': 0,
                'score': 0
            })

        for strategyKey in strategyData:
            strategy = strategyData[strategyKey]
            posData = strategy['pos_data']
            for i in range(length):
                result[i]['strategy_buy'] += 1 if posData[i] == 1 else 0
                result[i]['strategy_sell'] += 1 if posData[i] == -1 else 0
            
        for indicatorKey in indicatorData:
            indicator = indicatorData[indicatorKey]
            history = indicator['history']
            group = IndicatorGroup(Helper().getGroupByKey(indicatorKey))
            if group == IndicatorGroup.BASE:
                maTotal += 1
            elif group == IndicatorGroup.POWER:
                inTotal += 1

            for i in range(length):
                if group == IndicatorGroup.BASE:
                    result[i]['ma_buy'] += 1 if history[i] == 1 else 0
                    result[i]['ma_sell'] += 1 if history[i] == -1 else 0
                elif group == IndicatorGroup.POWER:
                    result[i]['in_buy'] += 1 if history[i] == 1 else 0
                    result[i]['in_sell'] += 1 if history[i] == -1 else 0
        
        for i in range(length):
            maV = (result[i]['ma_buy'] - result[i]['ma_sell'])/maTotal if maTotal > 0 else 0
            inV = (result[i]['in_buy'] - result[i]['in_sell'])/inTotal if inTotal > 0 else 0
            sV = (result[i]['strategy_buy'] - result[i]['strategy_sell'])/strategyTotal if strategyTotal > 0 else 0

            result[i]['ma_score'] = maV * 50 + 50
            result[i]['in_score'] = inV * 50 + 50
            result[i]['strategy_score'] = sV * 50 + 50

            normalScore = (maV + inV)/2*50 + 50
            score = normalScore

            if result[i]['strategy_sell'] > 0 and result[i]['strategy_buy'] > 0:
                if normalScore < 30:
                    score = normalScore * 0.7 + 30
                elif normalScore > 70:
                    score = normalScore * 0.7
            elif result[i]['strategy_buy'] > 0 and result[i]['strategy_sell'] == 0:
                score = normalScore * 0.3 + 70
            elif result[i]['strategy_buy'] == 0 and result[i]['strategy_sell'] > 0:
                score = normalScore * 0.3

            result[i]['score'] = float(format(score,'.2f'))
            # result[i]['score'] = float(format((maV + inV + 2 * sV)/4*50 + 50,'.2f'))
        return result
        