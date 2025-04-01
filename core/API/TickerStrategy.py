import json

from .MysqlHelper import MysqlHelper
from .Strategy import Strategy

import copy

class TickerStrategy:
    table = 'ticker_strategy'

    def __init__(self,connection):
        self.connection = connection
        self.strategy = Strategy(self.connection)

    def getItemsByTickerId(self,tickerId,klType):
        with self.connection.cursor() as cursor:
            sql = ("SELECT * FROM `%s` WHERE `ticker_id`=%s and `kl_type`='%s';") % (self.table,tickerId,klType)
            cursor.execute(sql)
            return cursor.fetchall()
    
    def getUpdateTimeByTickerId(self,tickerId,klType):
        with self.connection.cursor() as cursor:
            sql = ("SELECT min(`time_key`) as time FROM `%s` WHERE `ticker_id`=%s and `kl_type`='%s';") % (self.table,tickerId,klType)
            cursor.execute(sql)
            res = cursor.fetchone()
            return res['time']

    def getItemByTickerIdAndStrategyId(self,tickerId,strategyId,klType):
        with self.connection.cursor() as cursor:
            sql = ("SELECT * FROM `%s` WHERE `ticker_id`=%s and `strategy_id`=%s and `kl_type`='%s';") % (self.table,tickerId,strategyId,klType)
            cursor.execute(sql)
            return cursor.fetchone()

    def updateItem(self, tickerId, strategyKey, klType, timeKey, entity):
        data = copy.copy(entity)
        strategy = self.strategy.getItemByKey(strategyKey)
        strategyId = strategy['id']

        with self.connection.cursor() as cursor:
            result = self.getItemByTickerIdAndStrategyId(tickerId,strategyId,klType)
            data['data'] = '' if data['data'] is None else json.dumps(data['data'])
            data['pos_data'] = '' if data['pos_data'] is None else json.dumps(data['pos_data'])
            data['time_key'] = timeKey
            if result is None:
                data['ticker_id'] = tickerId
                data['strategy_id'] = strategyId
                data['kl_type'] = klType
                sql = MysqlHelper().insertEntity(self.table,data)
                cursor.execute(sql)
                self.connection.commit()
            else:
                delKeys = ['id','code','version','create_time','creator','mender','ticker_id','strategy_id','kl_type']
                for key in delKeys:
                    if key in data:
                        del data[key]
                
                condi = "`ticker_id`={ticker_id} and `strategy_id`={strategy_id} and `kl_type`='{kl_type}'".format(**{
                    'ticker_id': tickerId,
                    'strategy_id': strategyId,
                    'kl_type': klType
                })
                sql = MysqlHelper().update(self.table,data,condi)
                cursor.execute(sql)
                self.connection.commit()