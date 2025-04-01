from core.DB.DBHelper import DBHelper

class BaseAPI:
    def __init__(self):
        self.db = DBHelper()

    def _execute(self, sql: str, params=None) -> None:
        """执行SQL"""
        return self.db.execute(sql, params)

    def _query(self, sql: str, params=None) -> list:
        return self.db.query(sql, params)

    def _query_one(self, sql: str, params=None) -> dict:
        return self.db.query_one(sql, params)

    def _commit(self):
        """提交事务"""
        self.db.commit()

    def _rollback(self):
        """回滚事务"""
        self.db.rollback()

    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()
