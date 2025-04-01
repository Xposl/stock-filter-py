import copy
import pandas as pd

from core.Enum.TickerGroup import getGroupIdByCode

from .MysqlHelper import MysqlHelper


class Ticker:
    table = 'ticker'

    def __init__(self,connection):
        self.connection = connection

    def getUpdateTimeByCode(self,code,kltype):
        with self.connection.cursor() as cursor:
            sql = "SELECT IF(MIN(ts.`time_key`) < t.`update_date`,"
            sql += "if(MIN(ts.`time_key`) < MIN(ti.`time_key`),MIN(ts.`time_key`),MIN(ti.`time_key`)),"
            sql += "t.`update_date`) AS `update_time` "
            sql += "FROM `{table}` AS t "
            sql += "LEFT JOIN `ticker_strategy` AS `ts` ON `ts`.`ticker_id` = t.`id` and `ts`.`kl_type`= '{kltype}' "
            sql += "LEFT JOIN `ticker_indicator` AS `ti` ON `ti`.`ticker_id` = t.`id` and `ts`.`kl_type`= '{kltype}' "
            sql += "WHERE code = '{code}';"
            cursor.execute(sql.format(table = self.table,code = code, kltype = kltype))
            res = cursor.fetchone()
            return res['update_time']

    def getItemByCode(self,code):
        with self.connection.cursor() as cursor:
            sql = ("SELECT * FROM `%s` WHERE code = '%s';") % (self.table,code)
            cursor.execute(sql)
            return cursor.fetchone()
    
    def getItemLikeCode(self,code):
        with self.connection.cursor() as cursor:
            sql = ("SELECT * FROM `{table}` WHERE code like '%{code}';").format(table = self.table,code = code)
            cursor.execute(sql)
            return cursor.fetchone()

    def getAllItems(self):
        with self.connection.cursor() as cursor:
            sql = ("SELECT * FROM `%s`;") % self.table
            cursor.execute(sql)
            return cursor.fetchall()

    def getAllMapItems(self):
        with self.connection.cursor() as cursor:
            sql = ("SELECT * FROM `%s`;") % self.table
            cursor.execute(sql)
            tickers = cursor.fetchall()
            data = {}
            for ticker in tickers:
                data[ticker['code']] = ticker
            return data
            

    def getAllAvaiableItems(self,endDate=None):
        with self.connection.cursor() as cursor:
            sql = ''
            if endDate is None:
                sql = ("SELECT * FROM `%s` WHERE `is_deleted` = 0 and `status`= 1 ORDER BY `group_id`;") % (self.table)
            else:
                sql = ("SELECT * FROM `%s` WHERE `is_deleted` = 0 and (`listed_date` < '%s' or `listed_date` is NULL) and `status`= 1 ORDER BY `group_id`;") % (self.table,endDate)
            cursor.execute(sql)
            return cursor.fetchall()

    def getAllAvaiableItemsQuarter(self,endTime,page=1):
        with self.connection.cursor() as cursor:
            sql = ("SELECT count(*) as total FROM `%s` WHERE `is_deleted` = 0 and `status`= 1 and (`update_date` < '%s' OR `update_date` IS NULL) ORDER BY `group_id`;") % (self.table,endTime)
            cursor.execute(sql)
            res = cursor.fetchone()
            total = int(res['total'])
            limit = int(total/4) if total%4 == 0 else int(total/4) + 1
            offset = (int(page) - 1) * limit
            sql = ("SELECT * FROM `%s` WHERE `is_deleted` = 0 and `status`= 1 and ( `update_date` < '%s' OR `update_date` IS NULL ) ORDER BY `group_id` LIMIT %s OFFSET %s;") % (self.table,endTime,limit,offset)
            cursor.execute(sql)
            return cursor.fetchall()
    
    def getAllAvaiableItemsStartWith(self,startKey:str):
        with self.connection.cursor() as cursor:
            sql = "SELECT * FROM `{table}` WHERE `is_deleted` = 0 and `code` LIKE \"{startKey}%\" and `status`= 1;"
            cursor.execute(sql.format(**{
                'table': self.table,
                'startKey': startKey
            }))
            return cursor.fetchall()

    def insertItem(self,code,name, entity, commit=1):
        print('添加新的项目:'+code+' '+name)
        data = copy.copy(entity)
        with self.connection.cursor() as cursor:
            data['name'] = name
            data['group_id'] = getGroupIdByCode(code)
            data['code'] = code
            data['is_deleted'] = 0 if 'is_deleted' not in data else data['is_deleted']
            data['status'] = 1 if 'status' not in data else data['status']
            sql = MysqlHelper().insertEntity(self.table,data)
            cursor.execute(sql)
            if commit == 1:
                self.connection.commit()

    def updateItem(self,code,name,entity):
        data = copy.copy(entity)
        with self.connection.cursor() as cursor:
            data['name'] = name
            data['group_id'] = getGroupIdByCode(code)
            delKeys = ['id','code','version','create_time','creator','mender']
            for key in delKeys:
                if key in data:
                    del data[key]
            
            condi = " `code`=\"%s\"" % code
            sql = MysqlHelper().update(self.table,data,condi)
            cursor.execute(sql)
            self.connection.commit()
    
    def updateOrCreateItem(self,code,name,entity):
        with self.connection.cursor() as cursor:
            sql = "SELECT * FROM `%s` WHERE `code`='%s';" % (self.table,code)
            cursor.execute(sql)
            result = cursor.fetchone()
            if result is None:
                self.insertItem(code,name,entity)
            else:
                self.updateItem(code,name,entity)
    

    def deleteItemById(self,id):
        with self.connection.cursor() as cursor:
            sql = MysqlHelper().delete(self.table,"id = %s" %str(id))
            cursor.execute(sql)
            self.connection.commit()
    
    