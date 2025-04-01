

class Project:
    table = 'project'

    def __init__(self,connection):
        self.connection = connection

    def getItemsById(self,id):
        with self.connection.cursor() as cursor:
            sql = "SELECT * FROM `{table}` WHERE `id` = {id}".format(id=id)
            cursor.execute(sql)
            return cursor.fetchone()
