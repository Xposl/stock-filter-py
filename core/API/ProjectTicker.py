from .MysqlHelper import MysqlHelper


class ProjectTicker:
    table = 'project_ticker'

    def __init__(self,connection):
        self.connection = connection

    def getTickersByProjectId(self,projectId):
        with self.connection.cursor() as cursor:
            sql = "SELECT a.* FROM `ticker` as a "
            sql += "RIGHT JOIN `{table}` as b ON a.id = b.ticker_id "
            sql += "WHERE b.`project_id` = {projectId} AND b.`is_deleted` = 0;"
            cursor.execute(sql.format(table = self.table, projectId=projectId))
            return cursor.fetchall()
    
    def getItemByProjectIdTickerId(self,projectId,tickerId):
        with self.connection.cursor() as cursor:
            sql = "SELECT * FROM `{table}` WHERE `project_id` = {projectId} AND `ticker_id` = {tickerId};".format(table = self.table, projectId=projectId, tickerId=tickerId)
            cursor.execute(sql)
            return cursor.fetchone()

    def delItemsByProjectId(self,projectId):
        with self.connection.cursor() as cursor:
            sql = MysqlHelper().update(self.table,{'is_deleted':1},'`project_id` = {}'.format(projectId))
            cursor.execute(sql)
            self.connection.commit()

    def updateItem(self, projectId, tickerId,isDeleted=0):
        data = {
            'project_id': projectId,
            'ticker_id': tickerId,
            'is_deleted': isDeleted
        }
    
        with self.connection.cursor() as cursor:
            result = self.getItemByProjectIdTickerId(projectId,tickerId)
            if result is None:
                sql = MysqlHelper().insertEntity(self.table,data)
                cursor.execute(sql)
                self.connection.commit()
            else:
                delKeys = ['ticker_id','project_id']
                for key in delKeys:
                    if key in data:
                        del data[key]
                
                condi = "`project_id` = {projectId} AND `ticker_id` = {tickerId};".format(**{
                    'projectId': projectId,
                    'tickerId': tickerId
                })
                sql = MysqlHelper().update(self.table,data,condi)
                cursor.execute(sql)
                self.connection.commit()