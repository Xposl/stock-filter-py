
import datetime
from pymysql.converters import escape_string

class MysqlHelper:

    def insert(self,table,data):
        fieldArr = []
        valueArr = []
        for field in data:
            fieldArr.append(field)
            if data[field] == 'now()':
                valueArr.append("{"+field+"}")
            elif type(data[field]) == str or type(data[field]) == datetime.datetime:
                if type(data[field]) == str:
                    data[field] = escape_string(data[field])
                valueArr.append("'{"+field+"}'")
            else:
                valueArr.append("{"+field+"}")

        sql = "INSERT INTO `%s` (%s) VALUES (%s);" % (table,','.join(fieldArr),','.join(valueArr))
        return sql.format(**data)

    def insertItems(self,table,items):
        fieldArr = []
        valueArr = []
        for field in items[0]:
            fieldArr.append(field)

        for item in items:
            tempValue = []
            for field in item:
                if item[field] == 'now()':
                    tempValue.append("{"+field+"}")
                elif type(item[field]) == str or type(item[field]) == datetime.datetime:
                    if type(item[field]) == str:
                        item[field] = escape_string(item[field])
                    tempValue.append("'{"+field+"}'")
                else:
                    tempValue.append("{"+field+"}")
            valuesSql = "(%s)" % ','.join(tempValue)
            valueArr.append(valuesSql.format(**item))
        sql = "INSERT INTO `%s` (%s) VALUES %s" % (table,','.join(fieldArr),','.join(valueArr))
        return sql

    def insertEntity(self,table,data):
        data['version'] = 0
        data['create_time'] = 'now()'
        data['modify_time'] = 'now()'
        return self.insert(table,data)

    def update(self,table,data,condi):
        setArray = []

        for field in data:
            if data[field] is None:
                continue
            if data[field] == 'now()':
                setArray.append("`%s` = {%s}"%(field,field))
            elif type(data[field]) == str or type(data[field]) == datetime.datetime:
                if type(data[field]) == str:
                    data[field] = escape_string(data[field])
                setArray.append("`%s` = '{%s}'"%(field,field))
            else:
                setArray.append("`%s` = {%s}"%(field,field))
        sql = "UPDATE `%s` SET %s WHERE %s;" % (table,','.join(setArray),condi)
        return sql.format(**data)

    def delete(self,table,condi):
        sql = "DELETE FROM `"+table+"` "
        sql += 'WHERE '+condi+';'
        return sql


