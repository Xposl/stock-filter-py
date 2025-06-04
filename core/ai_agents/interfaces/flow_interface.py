#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
流程接口定义

定义所有AI流程的标准接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pocketflow import Flow

class BaseFlow(ABC):
    """流程基类 - 基于PocketFlow的标准化包装"""
    
    def __init__(self, flow_name: str):
        self.flow_name = flow_name
        self.flow: Flow = None
        
    @abstractmethod
    def build_flow(self) -> Flow:
        """构建PocketFlow流程"""
        pass
        
    @abstractmethod
    def execute_flow(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行流程"""
        pass
    
    def get_flow_info(self) -> Dict[str, Any]:
        """获取流程信息"""
        return {
            "name": self.flow_name,
            "class_name": self.__class__.__name__
        } 