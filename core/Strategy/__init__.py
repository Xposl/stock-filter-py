from .ARTDLStrategy import ARTDLStrategy
from .MABaseStrategy import MABaseStrategy
from .CCIMaStrategy import CCIMaStrategy
from .CCIWmaStrategy import CCIWmaStrategy
from .BollDLStrategy import BollDLStrategy

from core.utils import UtilsHelper
import math

defaultStrategies = [
    BollDLStrategy(),
    CCIWmaStrategy(),
    CCIMaStrategy(),
    ARTDLStrategy(),
    MABaseStrategy()
]

class Strategy:
    group = []
    groupMap = {}
    profit_init = 100000

    def __init__(self,group=None):
        if group is not None:
            self.group = group
        else:
            self.group = defaultStrategies
        for item in self.group:
            self.groupMap[item.getKey()] = item

    def calculate(self,klData):
        result = {}
        for item in self.group:
            res = self.calculateByKey(item.getKey(),klData)
            result[item.getKey()] = res
        return result

    def calculateByKey(self,strategyKey, klData):
        if self.groupMap[strategyKey] is None:
            raise Exception('error，找不到策略',strategyKey)
        return self.calculateStrategy(self.groupMap[strategyKey],klData)

    def calculateStrategy(self,strategyObj, klData):
        result = {
            'net_profit': 0, #利润
            'net_profit_pre': 0, #利润率
            'gross_profit': 0, #毛利润
            'gross_profit_pre': 0, #毛利润率
            'gross_loss': 0, #毛损失
            'gross_loss_pre': 0, #毛损失率
            'hold_return':0, #买入到今利润
            'hold_return_pre':0, #买入到今利润率
            'trades':0, #交易笔数
            'win_trades':0, #挣钱交易
            'loss_trades':0, #亏损交易
            'keep_days': 0, #平均持仓时间
            'win_keep_days': 0, #盈利平均持仓时间
            'loss_keep_days': 0, #亏损平均持仓时间
            'profitable':0, #胜率
            'avg_win_pre':0, #平均盈利率
            'avg_loss_pre':0, #平均亏损率
            'ratio':0, #盈亏比
            'status':0, #当前状态-1:做空 1:做多
            'days':0, #当前状态持续时间
            'profit':0 #当前状态利润
        }
        length = len(klData)
        status = 0  ## 当前交易状态
        unit = 1    ## 交易股份数量
        profit = 0  ## 当前浮盈
        iniPrice = None ## 第一次买入价格
        startPrice = None ## 本次交易买入价格
        startTime = None ## 本次交易买入时机
        startKIndex = 0 ## 本次交易开始的K线
        close = 0 ## 最后交易日的价格

        posData = strategyObj.calculate(klData)
        if len(posData) != length:
            raise Exception('策略数据错误,数据长度不符',length,len(posData))
        
        tradeData = []
        for i in range(length):
            openP = klData[i]['open']
            close = klData[i]['close']

            # 出现信号第二天，进行操作
            if result['days'] == 1 and status == 1:
                unit = UtilsHelper().calcuInteger(self.profit_init,abs(openP))
                if unit > 0: #判断资金是否足够买入
                    # 做多,以开盘价进行操作
                    if iniPrice is None:
                        iniPrice = openP
                    startPrice = openP
                    startKIndex = i
                    startTime = klData[i]['time_key']
                    profit = 0

            elif result['days'] == 1 and status == -1:
                # 清仓
                if startPrice is not None and startKIndex is not None:
                    # 浮动利率
                    profit = (openP - startPrice) * unit
                    keepDays = i - startKIndex + 1
                    startKIndex = None
                    if profit >= 0:
                        result['win_trades'] = result['win_trades'] + 1
                        result['gross_profit'] = result['gross_profit'] + profit
                        result['win_keep_days'] = keepDays
                    else:
                        result['gross_loss'] = result['gross_loss'] - profit
                        result['loss_trades'] = result['loss_trades'] + 1
                        result['loss_keep_days'] = keepDays
                    
                    tradeData.append({
                        'startDate': startTime.strftime('%Y-%m-%d %H:%M:%S') if startTime is not None else '',
                        'endDate': klData[i]['time_key'].strftime('%Y-%m-%d %H:%M:%S'),
                        'buy': startPrice,
                        'unit': unit,
                        'sell': openP,
                        'keepDays': keepDays,
                        'profit': profit,
                        'percent': UtilsHelper().calcuPercent((openP - startPrice),abs(startPrice))
                    })

                # 记录做空时的状态
                startPrice = openP
                startTime = klData[i]['time_key']
                profit = 0
                unit = UtilsHelper().calcuInteger(self.profit_init,abs(startPrice))
            
            ## 如果交易状态发生变更，表示出现买卖点
            if posData[i] != status:
                result['days'] = 1
                status = posData[i]
                ##  如果是最后一个交易日，清空当前交易状态
                if i == length - 1 and startPrice is not None:
                    profit = 0
            else:
                result['days'] += 1
                ##  如果是最后一个交易日，计算浮动盈亏
                if i == length - 1 and startPrice is not None:
                    profit = (close - startPrice) * unit
                    result['days'] = result['days'] - 1

        
        result['keep_days'] = result['win_keep_days'] + result['loss_keep_days']
        result['trades'] = result['win_trades'] + result['loss_trades']
        result['gross_profit'] = round(result['gross_profit'],2)
        result['gross_loss'] = round(result['gross_loss'],2)
        result['net_profit'] = round(result['gross_profit'] - result['gross_loss'],2)
        result['net_profit_pre'] = round(result['net_profit']/self.profit_init * 100,2)
        result['gross_profit_pre'] = round(result['gross_profit']/self.profit_init * 100,2)
        result['gross_loss_pre'] = round(result['gross_loss']/self.profit_init * 100,2)

        if iniPrice is not None:
            unit = math.floor(self.profit_init/iniPrice) if iniPrice > 0 else self.profit_init
            result['hold_return'] = (close - iniPrice) * unit
            result['hold_return_pre'] = round(result['hold_return']/self.profit_init * 100,2)
        
        result['avg_win_pre'] = UtilsHelper().calcuPercent(result['gross_profit_pre'],result['win_trades'])/100
        result['avg_loss_pre'] = UtilsHelper().calcuPercent(result['gross_loss_pre'],result['loss_trades'])/100
        result['profitable'] = UtilsHelper().calcuPercent(result['win_trades'],result['trades'])
        result['ratio'] = UtilsHelper().calcuPercent(result['avg_win_pre'],result['avg_loss_pre'])

        result['data'] = tradeData
        result['pos_data'] = posData
        result['profit'] = round(profit,2)
        result['status'] = status
        return result
            