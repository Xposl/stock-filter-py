import copy

from .MysqlHelper import MysqlHelper


class TickerDayLine:
    table = 'ticker_day_line'

    def __init__(self,connection):
        self.connection = connection

    def getItemsByTickerId(self,tickerId):
        with self.connection.cursor() as cursor:
            sql = ("SELECT * FROM `%s` WHERE ticker_id = '%s';") % (self.table,str(tickerId))
            cursor.execute(sql)
            kLineData = cursor.fetchall()
            return kLineData
    
    def clearItemsByTickerId(self,tickerId):
        with self.connection.cursor() as cursor:
            sql = MysqlHelper().delete(self.table,"ticker_id = %s" %tickerId)
            cursor.execute(sql)
            self.connection.commit()

    def insertItem(self,item):
        with self.connection.cursor() as cursor:
            sql = MysqlHelper().insert(self.table,item)
            cursor.execute(sql)
            self.connection.commit()

    def updateItems(self,tickerId,items):
        self.clearItemsByTickerId(tickerId)
        index = 0
        insertItems = []
        for item in items:
            data = copy.copy(item)
            id = tickerId * 1000 + index
            data['id'] = id
            data['ticker_id'] = tickerId
            insertItems.append(data)
            index += 1
        with self.connection.cursor() as cursor:
            sql = MysqlHelper().insertItems(self.table,insertItems)
            cursor.execute(sql)
            self.connection.commit()
   