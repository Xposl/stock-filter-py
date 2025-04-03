from core.Indicator import Indicator as Helper
from core.enum.indicator_group import IndicatorGroup
import numpy as np
from scipy import stats

class NormalScore:

    def calculate(self,ticker,kLineData,strategyData,indicatorData,valuationData):
        tickerId = ticker.id
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
                'id': kLineData[i].get('id', 0),  # 使用get方法，如果没有id键则默认为0
                'time_key': kLineData[i]['time_key'].strftime('%Y-%m-%d') if hasattr(kLineData[i]['time_key'], 'strftime') else kLineData[i]['time_key'],
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
                'score': 0,
                'raw_score': 0  # 添加原始得分，不受上下限约束
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
        
        # 收集原始分数以计算Z分数
        raw_scores = []
        
        for i in range(length):
            maV = (result[i]['ma_buy'] - result[i]['ma_sell'])/maTotal if maTotal > 0 else 0
            inV = (result[i]['in_buy'] - result[i]['in_sell'])/inTotal if inTotal > 0 else 0
            sV = (result[i]['strategy_buy'] - result[i]['strategy_sell'])/strategyTotal if strategyTotal > 0 else 0

            # 保留传统评分用于参考
            result[i]['ma_score'] = maV * 50 + 50
            result[i]['in_score'] = inV * 50 + 50
            result[i]['strategy_score'] = sV * 50 + 50

            # 计算不受限的原始得分
            normalScore = (maV + inV)/2
            raw_score = normalScore
            
            # 策略影响因子
            strategy_factor = 0
            if result[i]['strategy_sell'] > 0 and result[i]['strategy_buy'] > 0:
                # 买卖信号同时存在，减弱信号强度
                strategy_factor = 0
            elif result[i]['strategy_buy'] > 0 and result[i]['strategy_sell'] == 0:
                # 只有买入信号，增强正面评分
                strategy_factor = 1
            elif result[i]['strategy_buy'] == 0 and result[i]['strategy_sell'] > 0:
                # 只有卖出信号，增强负面评分
                strategy_factor = -1
            
            # 将策略因子融入原始评分
            raw_score = raw_score + strategy_factor * 0.5
            
            # 保存原始评分，不进行0-100的归一化
            result[i]['raw_score'] = float(format(raw_score, '.4f'))
            raw_scores.append(raw_score)
        
        # 计算Z-分数 (如果数据量足够)
        if len(raw_scores) > 5:
            mean_score = np.mean(raw_scores)
            std_score = np.std(raw_scores) if np.std(raw_scores) > 0 else 1.0
            
            for i in range(length):
                z_score = (result[i]['raw_score'] - mean_score) / std_score
                result[i]['z_score'] = float(format(z_score, '.4f'))
                # 将Z-分数转换为百分位数 (0-100)
                percentile = stats.norm.cdf(z_score) * 100
                result[i]['score'] = float(format(percentile, '.4f'))
        return result