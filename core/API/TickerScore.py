from .MysqlHelper import MysqlHelper

class TickerScore:
    table = 'ticker_score'

    def __init__(self,connection):
        self.connection = connection

    def getItemsByTickerId(self,tickerId):
        with self.connection.cursor() as cursor:
            sql = ("SELECT * FROM `%s` WHERE `ticker_id`=%s;") % (self.table,tickerId)
            cursor.execute(sql)
            return cursor.fetchall()

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
        if items is not None and len(items) > 0:
            for item in items:
                id = tickerId * 1000 + index
                item['id'] = id
                item['ticker_id'] = tickerId
                insertItems.append(item)
                index += 1
            with self.connection.cursor() as cursor:
                sql = MysqlHelper().insertItems(self.table,insertItems)
                cursor.execute(sql)
                self.connection.commit()
   