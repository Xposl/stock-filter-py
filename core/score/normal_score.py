from typing import Optional, List
from core.indicator import Indicator as Helper
from core.enum.indicator_group import IndicatorGroup
import numpy as np
from scipy import stats
from core.models.ticker import Ticker
from core.models.ticker_score import TickerScore
from core.score.base_score import BaseScore

class NormalScore(BaseScore):

    def calculate(self,ticker: Ticker,kLineData: Optional[list]=None,strategyData: Optional[list]=None,indicatorData: Optional[list]=None,valuationData: Optional[list]=None) -> List[TickerScore]:
        """
        计算普通评分
        """
        tickerId = ticker.id
        length = len(kLineData)
        if length == 0:
            print('无数据')
            return []
        
        result = []
        maTotal = 0
        inTotal = 0
        strategyTotal = len(strategyData)
        for i in range(length):
            # 处理不同数据类型（KLine对象或字典）
            kline_item = kLineData[i]
            if hasattr(kline_item, 'time_key'):  # KLine对象
                time_key = kline_item.time_key
                item_id = 0  # KLine对象没有id字段
            else:  # 字典
                time_key = kline_item.get('time_key', '')
                item_id = kline_item.get('id', 0)
            
            # 格式化时间键
            if hasattr(time_key, 'strftime'):
                time_key = time_key.strftime('%Y-%m-%d')
                
            result.append({
                'id': item_id,
                'time_key': time_key,
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
        
        # 将字典列表转换为TickerScore对象列表
        ticker_scores = []
        for data in result:
            # 将附加数据存储在history字段中
            history_data = {
                'raw_score': data.get('raw_score', 0),
                'z_score': data.get('z_score', 0)
            }
            
            ticker_score = TickerScore(
                id=data.get('id', 0),
                time_key=data['time_key'],
                ticker_id=data['ticker_id'],
                ma_buy=data['ma_buy'],
                ma_sell=data['ma_sell'],
                ma_score=data['ma_score'],
                in_buy=data['in_buy'],
                in_sell=data['in_sell'],
                in_score=data['in_score'],
                strategy_buy=data['strategy_buy'],
                strategy_sell=data['strategy_sell'],
                strategy_score=data['strategy_score'],
                score=data['score'],
                history=history_data  # 将附加数据存储在history中
            )
            ticker_scores.append(ticker_score)
        
        return ticker_scores