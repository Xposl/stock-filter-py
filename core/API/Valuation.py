from .MysqlHelper import MysqlHelper

class Valuation:
    table = 'valuation'

    def __init__(self,connection):
        self.connection = connection

    def insertItem(self,key):
        with self.connection.cursor() as cursor:
            data = {
                'name': key[:-10],
                'valuation_key': key,
                'is_deleted': 0, 
                'status': 1
            }
            sql = MysqlHelper().insertEntity(self.table,data)
            cursor.execute(sql)
            self.connection.commit()

    def getItemByKey(self,key):
        with self.connection.cursor() as cursor:
            sql = ("SELECT * FROM `%s` WHERE valuation_key = '%s';") % (self.table,key)
            cursor.execute(sql)
            result = cursor.fetchone()
            if result is None:
                self.insertItem(key)
                return self.getItemByKey(key)
            return result