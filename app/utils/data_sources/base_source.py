"""
数据源模块初始化文件
"""
from abc import ABC, abstractmethod
from typing import Optional

from core.schema.k_line import KLine


class BaseSource(ABC):
    """K线数据源基类，定义了数据源需要实现的接口"""

    @abstractmethod
    def get_kl_on_time(self, code: str) -> Optional[KLine]:
        """获取实时K线数据

        Returns:
            KLine: 实时K线数据，失败返回None
        """
        pass

    @abstractmethod
    def get_kl(
        self, code: str, start_date: str, end_date: Optional[str] = None
    ) -> list[KLine]:
        """获取K线数据

        Returns:
            List[KLine]: K线数据列表，失败返回None
        """
        pass
