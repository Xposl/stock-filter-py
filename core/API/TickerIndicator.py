import json
import copy

from .MysqlHelper import MysqlHelper
from .Indicator import Indicator

class TickerIndicator:
    table = 'ticker_indicator'

    def __init__(self,connection):
        self.connection = connection
        self.indicator = Indicator(connection)

    def getItemsByTickerId(self,tickerId,klType):
        with self.connection.cursor() as cursor:
            sql = "SELECT a.*, b.indicator_group as indicator_group FROM `%s` as a "
            sql += "LEFT JOIN `indicator` as b ON a.indicator_id = b.id "
            sql += " WHERE a.`ticker_id`=%s and a.`kl_type`='%s';"
            cursor.execute(sql% (self.table,tickerId,klType))
            return cursor.fetchall()

    def getUpdateTimeByTickerId(self,tickerId,klType):
        with self.connection.cursor() as cursor:
            sql = ("SELECT min(`time_key`) as time FROM `%s` WHERE `ticker_id`=%s and `kl_type`='%s';") % (self.table,tickerId,klType)
            cursor.execute(sql)
            res = cursor.fetchone()
            return res['time']

    def getItemByTickerIdAndIndicatorId(self,tickerId,indicatorId,klType):
        with self.connection.cursor() as cursor:
            sql = ("SELECT * FROM `%s` WHERE `ticker_id`=%s and `indicator_id`=%s and `kl_type`='%s';") % (self.table,tickerId,indicatorId,klType)
            cursor.execute(sql)
            return cursor.fetchone()

    def updateItem(self, tickerId, indicatorKey, klType, timeKey, entity):
        data = copy.copy(entity)
        indicator = self.indicator.getItemByKey(indicatorKey)
        indicatorId = indicator['id']

        with self.connection.cursor() as cursor:
            result = self.getItemByTickerIdAndIndicatorId(tickerId,indicatorId,klType)
            data['history'] = '' if data['history'] is None else json.dumps(data['history'])
            data['time_key'] = timeKey
            if result is None:
                data['ticker_id'] = tickerId
                data['indicator_id'] = indicatorId
                data['kl_type'] = klType
                sql = MysqlHelper().insertEntity(self.table,data)
                cursor.execute(sql)
                self.connection.commit()
            else:
                delKeys = ['id','code','version','create_time','creator','mender','ticker_id','indicator_id','kl_type']
                for key in delKeys:
                    if key in data:
                        del data[key]
                
                condi = "`ticker_id`={ticker_id} and `indicator_id`={indicator_id} and `kl_type`='{kl_type}'".format(**{
                    'ticker_id': tickerId,
                    'indicator_id': indicatorId,
                    'kl_type': klType
                })
                sql = MysqlHelper().update(self.table,data,condi)
                cursor.execute(sql)
                self.connection.commit()

    def updateItems(self, tickerId, indicators, klType, timeKey):
        with self.connection.cursor() as cursor:
            for indicatorKey in indicators:
                entity = indicators[indicatorKey]
                data = copy.copy(entity)
                indicator = self.indicator.getItemByKey(indicatorKey)
                indicatorId = indicator['id']

                result = self.getItemByTickerIdAndIndicatorId(tickerId,indicatorId,klType)
                data['history'] = '' if data['history'] is None else json.dumps(data['history'])
                data['time_key'] = timeKey
                if result is None:
                    data['ticker_id'] = tickerId
                    data['indicator_id'] = indicatorId
                    data['kl_type'] = klType
                    sql = MysqlHelper().insertEntity(self.table,data)
                    cursor.execute(sql)
                else:
                    delKeys = ['id','code','version','create_time','creator','mender','ticker_id','indicator_id','kl_type']
                    for key in delKeys:
                        if key in data:
                            del data[key]
                    
                    condi = "`ticker_id`={ticker_id} and `indicator_id`={indicator_id} and `kl_type`='{kl_type}'".format(**{
                        'ticker_id': tickerId,
                        'indicator_id': indicatorId,
                        'kl_type': klType
                    })
                    sql = MysqlHelper().update(self.table,data,condi)
                    cursor.execute(sql)
            self.connection.commit()