"""
雪球客户端工厂
统一创建和管理不同类型的雪球客户端
"""

import logging
from enum import Enum
from typing import Any, Optional, Union

import aiohttp

from .xueqiu_base_client import XueqiuBaseClient
from .xueqiu_stock_client import XueqiuStockClient

logger = logging.getLogger(__name__)


class XueqiuClientType(Enum):
    """雪球客户端类型枚举"""

    NEWS = "news"
    STOCK = "stock"


class XueqiuClientFactory:
    """雪球客户端工厂"""

    def __init__(self, session: Optional[aiohttp.ClientSession] = None):
        """
        初始化客户端工厂

        Args:
            session: 可选的共享aiohttp会话
        """
        self.session = session
        self._clients: dict[str, XueqiuBaseClient] = {}
        self._config = self._get_default_config()

    def _get_default_config(self) -> dict[str, Any]:
        """获取默认配置"""
        return {
            "news": {"max_retries": 3, "timeout": 30, "enable_cache": True},
            "stock": {"max_retries": 2, "timeout": 15, "enable_cache": True},
        }

    def create_client(
        self,
        client_type: Union[XueqiuClientType, str],
        session: Optional[aiohttp.ClientSession] = None,
    ) -> XueqiuBaseClient:
        """
        创建雪球客户端

        Args:
            client_type: 客户端类型
            session: 可选的aiohttp会话

        Returns:
            对应类型的雪球客户端
        """
        # 标准化客户端类型
        if isinstance(client_type, str):
            client_type = XueqiuClientType(client_type)

        client_key = client_type.value

        # 如果已经存在该类型的客户端，返回现有实例
        if client_key in self._clients:
            logger.debug(f"返回现有的 {client_key} 客户端")
            return self._clients[client_key]

        # 使用传入的session或工厂的session
        client_session = session or self.session

        # 根据类型创建客户端
        if client_type == XueqiuClientType.STOCK:
            client = XueqiuStockClient(session=client_session)
        else:
            raise ValueError(f"不支持的客户端类型: {client_type}")

        # 缓存客户端实例
        self._clients[client_key] = client

        logger.info(f"创建新的 {client_key} 客户端")
        return client

    def get_stock_client(
        self, session: Optional[aiohttp.ClientSession] = None
    ) -> XueqiuStockClient:
        """
        获取股票客户端

        Args:
            session: 可选的aiohttp会话

        Returns:
            雪球股票客户端
        """
        return self.create_client(XueqiuClientType.STOCK, session)

    async def create_async_client(
        self, client_type: Union[XueqiuClientType, str], auto_session: bool = True
    ) -> XueqiuBaseClient:
        """
        创建异步雪球客户端

        Args:
            client_type: 客户端类型
            auto_session: 是否自动创建aiohttp会话

        Returns:
            配置好的雪球客户端
        """
        session = None
        if auto_session and not self.session:
            # 创建优化的aiohttp会话
            connector = aiohttp.TCPConnector(
                limit=100, limit_per_host=30, ssl=False  # 处理SSL证书问题
            )
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            session = aiohttp.ClientSession(connector=connector, timeout=timeout)
            self.session = session

        return self.create_client(client_type, self.session)

    def configure_client(
        self, client_type: Union[XueqiuClientType, str], config: dict[str, Any]
    ) -> None:
        """
        配置特定类型的客户端

        Args:
            client_type: 客户端类型
            config: 配置字典
        """
        if isinstance(client_type, str):
            client_type = XueqiuClientType(client_type)

        client_key = client_type.value

        if client_key not in self._config:
            self._config[client_key] = {}

        self._config[client_key].update(config)
        logger.info(f"更新 {client_key} 客户端配置: {config}")

    def get_client_config(
        self, client_type: Union[XueqiuClientType, str]
    ) -> dict[str, Any]:
        """
        获取客户端配置

        Args:
            client_type: 客户端类型

        Returns:
            客户端配置字典
        """
        if isinstance(client_type, str):
            client_type = XueqiuClientType(client_type)

        return self._config.get(client_type.value, {})

    async def cleanup(self):
        """清理资源"""
        try:
            # 关闭所有客户端
            for client in self._clients.values():
                if (
                    hasattr(client, "session")
                    and client.session
                    and client._own_session
                ):
                    await client.session.close()

            # 关闭工厂的session
            if self.session:
                await self.session.close()
                self.session = None

            # 清空客户端缓存
            self._clients.clear()

            logger.info("雪球客户端工厂资源清理完成")

        except Exception as e:
            logger.error(f"清理雪球客户端工厂资源失败: {e}")

    def __del__(self):
        """析构函数"""
        # 在对象销毁时确保资源已清理
        if self._clients or self.session:
            logger.warning("雪球客户端工厂未正确清理，建议使用 async with 或手动调用 cleanup()")


# 全局工厂实例
_default_factory: Optional[XueqiuClientFactory] = None


def get_default_factory() -> XueqiuClientFactory:
    """获取默认的雪球客户端工厂"""
    global _default_factory
    if _default_factory is None:
        _default_factory = XueqiuClientFactory()
    return _default_factory


def create_stock_client(
    session: Optional[aiohttp.ClientSession] = None,
) -> XueqiuStockClient:
    """
    快速创建股票客户端

    Args:
        session: 可选的aiohttp会话

    Returns:
        雪球股票客户端
    """
    factory = get_default_factory()
    return factory.get_stock_client(session)


async def cleanup_default_factory():
    """清理默认工厂资源"""
    global _default_factory
    if _default_factory:
        await _default_factory.cleanup()
        _default_factory = None
