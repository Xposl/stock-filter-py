#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
节点接口定义

定义所有AI节点的标准接口，基于PocketFlow框架
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pocketflow import Node

class BaseNode(Node):
    """节点基类 - 继承PocketFlow的Node，添加标准化接口"""
    
    def __init__(self):
        super().__init__()
        self.node_type = "base"
        self.description = ""
    
    def get_node_info(self) -> Dict[str, Any]:
        """获取节点信息"""
        return {
            "type": self.node_type,
            "description": self.description,
            "class_name": self.__class__.__name__
        }

class BaseAnalysisNode(BaseNode):
    """分析节点基类"""
    
    def __init__(self):
        super().__init__()
        self.node_type = "analysis"
    
    @abstractmethod
    def analyze(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行分析任务"""
        pass

class BaseDataIngestionNode(BaseNode):
    """数据摄取节点基类"""
    
    def __init__(self):
        super().__init__()
        self.node_type = "data_ingestion"
    
    @abstractmethod
    def ingest(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行数据摄取"""
        pass

class BaseDecisionNode(BaseNode):
    """决策节点基类"""
    
    def __init__(self):
        super().__init__()
        self.node_type = "decision"
    
    @abstractmethod
    def decide(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行决策"""
        pass

class BaseOutputNode(BaseNode):
    """输出节点基类"""
    
    def __init__(self):
        super().__init__()
        self.node_type = "output"
    
    @abstractmethod
    def output(self, result_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行输出"""
        pass 