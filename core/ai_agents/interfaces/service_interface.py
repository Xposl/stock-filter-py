#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
服务接口定义

定义所有核心服务的标准接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseService(ABC):
    """服务基类"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.is_initialized = False
    
    @abstractmethod
    async def initialize(self) -> None:
        """初始化服务"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """清理服务资源"""
        pass
    
    def get_service_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            "name": self.service_name,
            "class_name": self.__class__.__name__,
            "is_initialized": self.is_initialized
        } 