import copy

from .MysqlHelper import MysqlHelper
from .Valuation import Valuation

class TickerValuation:
    table = 'ticker_valuation'

    def __init__(self,connection):
        self.connection = connection
        self.valuation = Valuation(connection)

    def getItemsByTickerId(self,tickerId):
        with self.connection.cursor() as cursor:
            sql = "SELECT a.* FROM `%s` as a "
            sql += "LEFT JOIN `valuation` as b ON a.valuation_id = b.id "
            sql += " WHERE a.`ticker_id`=%s;"
            cursor.execute(sql% (self.table,tickerId))
            return cursor.fetchall()
    
    def getItemByTickerIdAndKey(self,tickerId,valuationKey):
        with self.connection.cursor() as cursor:
            sql = "SELECT a.* FROM `%s` as a "
            sql += "LEFT JOIN `valuation` as b ON a.valuation_id = b.id "
            sql += " WHERE a.`ticker_id`=%s and `valuation_key` = '%s';"
            cursor.execute(sql% (self.table,tickerId,valuationKey))
            return cursor.fetchone()

    def getUpdateTimeByTickerId(self,tickerId):
        with self.connection.cursor() as cursor:
            sql = ("SELECT min(`time_key`) as time FROM `%s` WHERE `ticker_id`=%s;") % (self.table,tickerId)
            cursor.execute(sql)
            res = cursor.fetchone()
            return res['time']

    def getItemByTickerIdAndIndicatorId(self,tickerId,valuationId):
        with self.connection.cursor() as cursor:
            sql = ("SELECT * FROM `%s` WHERE `ticker_id`=%s and `valuation_id`=%s;") % (self.table,tickerId,valuationId)
            cursor.execute(sql)
            return cursor.fetchone()

    def updateItem(self, tickerId, valuationKey, timeKey, entity):
        data = copy.copy(entity)
        valuation = self.valuation.getItemByKey(valuationKey)
        valuationId = valuation['id']

        with self.connection.cursor() as cursor:
            result = self.getItemByTickerIdAndIndicatorId(tickerId,valuationId)
            data['time_key'] = timeKey
            if result is None:
                data['ticker_id'] = tickerId
                data['valuation_id'] = valuationId
                sql = MysqlHelper().insertEntity(self.table,data)
                cursor.execute(sql)
                self.connection.commit()
            else:
                delKeys = ['id','code','version','create_time','creator','mender','ticker_id','valuation_id']
                for key in delKeys:
                    if key in data:
                        del data[key]
                
                condi = "`ticker_id`={ticker_id} and `valuation_id`={valuation_id}".format(**{
                    'ticker_id': tickerId,
                    'valuation_id': valuationId
                })
                sql = MysqlHelper().update(self.table,data,condi)
                cursor.execute(sql)
                self.connection.commit()