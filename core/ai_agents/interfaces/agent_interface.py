#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
代理接口定义

定义所有AI代理的标准接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class AgentConfig:
    """代理配置"""
    agent_name: str
    agent_type: str
    llm_client: Any
    config_params: Dict[str, Any]

class BaseAgent(ABC):
    """代理基类 - 定义所有代理的通用接口"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.agent_name = config.agent_name
        self.agent_type = config.agent_type
        
    @abstractmethod
    async def execute_async(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """异步执行代理任务"""
        pass
        
    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """同步执行代理任务"""
        pass
    
    def get_capabilities(self) -> List[str]:
        """获取代理能力列表"""
        return []
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取代理元数据"""
        return {
            "name": self.agent_name,
            "type": self.agent_type,
            "capabilities": self.get_capabilities()
        } 