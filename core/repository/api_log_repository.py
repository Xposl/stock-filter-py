from datetime import datetime
from typing import Any, Optional

from core.database.db_adapter import DbAdapter
from core.models.api_log import ApiLog


class ApiLogRepository:
    table = "api_log"

    def __init__(self, db_connection: Optional[Any] = None):
        if db_connection:
            self.db = db_connection
        else:
            self.db = DbAdapter()

    def insert(self, log: ApiLog) -> int:
        sql = f"""
        INSERT INTO {self.table} (path, method, params, exception, traceback, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        values = (
            log.path,
            log.method,
            log.params,
            log.exception,
            log.traceback,
            log.created_at.strftime("%Y-%m-%d %H:%M:%S")
            if isinstance(log.created_at, datetime)
            else log.created_at,
        )
        self.db.execute(sql, values)
        self.db.commit()
        return self.db.cursor.lastrowid
