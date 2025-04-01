from .MysqlHelper import MysqlHelper

from core.Indicator import Indicator as Helper

class Indicator:
    table = 'indicator'

    def __init__(self,connection):
        self.connection = connection
        self.helper = Helper()

    def insertItem(self,key):
        with self.connection.cursor() as cursor:
            data = {
                'name': key[:-10],
                'indicator_key': key,
                'is_deleted': 0, 
                'status': 1,
                'indicator_group': Helper().getGroupByKey(key)
            }
            sql = MysqlHelper().insertEntity(self.table,data)
            cursor.execute(sql)
            self.connection.commit()

    def getItemByKey(self,key):
        with self.connection.cursor() as cursor:
            sql = ("SELECT * FROM `%s` WHERE indicator_key = '%s';") % (self.table,key)
            cursor.execute(sql)
            result = cursor.fetchone()
            if result is None:
                self.insertItem(key)
                return self.getItemByKey(key)
            return result