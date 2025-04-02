#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Optional, Union, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict, Json

class TickerStrategyBase(BaseModel):
    """策略基础模型，包含共有字段"""
    ticker_id: int = Field(..., description="股票ID")
    strategy_key: str = Field(..., description="策略键，使用Strategy的getKey值")
    kl_type: str = Field(..., description="K线类型")
    time_key: str = Field(..., description="时间键")
    data: Optional[Union[List[Any], Dict[str, Any]]] = Field(default=None, description="策略数据")
    pos_data: Optional[Union[List[Any], Dict[str, Any]]] = Field(default=None, description="持仓数据")
    status: Optional[int] = Field(default=1, description="状态")
    
    model_config = ConfigDict(from_attributes=True)

class TickerStrategyCreate(TickerStrategyBase):
    """用于创建策略的模型"""
    pass

class TickerStrategyUpdate(BaseModel):
    """用于更新策略的模型，所有字段都是可选的"""
    time_key: Optional[str] = Field(default=None, description="时间键")
    data: Optional[Union[List[Any], Dict[str, Any]]] = Field(default=None, description="策略数据")
    pos_data: Optional[Union[List[Any], Dict[str, Any]]] = Field(default=None, description="持仓数据")
    status: Optional[int] = Field(default=None, description="状态")
    
    model_config = ConfigDict(from_attributes=True)

class TickerStrategy(TickerStrategyBase):
    """完整的策略模型，包含ID"""
    id: int = Field(..., description="ID")
    code: Optional[str] = Field(default=None, description="代码")
    version: Optional[int] = Field(default=1, description="版本号")
    create_time: Optional[datetime] = Field(default_factory=datetime.now, description="创建时间")
    
    model_config = ConfigDict(from_attributes=True)

# 用于序列化和反序列化的辅助函数
def ticker_strategy_to_dict(strategy: Union[TickerStrategy, TickerStrategyCreate, TickerStrategyUpdate]) -> dict:
    """
    将TickerStrategy模型转换为字典，用于数据库操作
    
    Args:
        strategy: TickerStrategy、TickerStrategyCreate或TickerStrategyUpdate模型
    
    Returns:
        字典表示
    """
    result = {}
    
    if isinstance(strategy, (TickerStrategyCreate, TickerStrategyUpdate)):
        result = strategy.model_dump(exclude_unset=True, exclude_none=True)
    else:
        result = strategy.model_dump(exclude_none=True)
    
    # 处理JSON字段
    if 'data' in result and result['data'] is not None:
        import json
        result['data'] = json.dumps(result['data'])
    
    if 'pos_data' in result and result['pos_data'] is not None:
        import json
        result['pos_data'] = json.dumps(result['pos_data'])
        
    return result

def dict_to_ticker_strategy(data: dict) -> TickerStrategy:
    """
    将字典转换为TickerStrategy模型，处理各种数据类型转换和默认值
    
    Args:
        data: 来自数据库的字典数据
    
    Returns:
        TickerStrategy模型实例
    """
    # 创建数据的副本，避免修改原始数据
    processed_data = data.copy()
    
    # 处理JSON字段
    for json_field in ['data', 'pos_data']:
        if json_field in processed_data:
            json_value = processed_data[json_field]
            
            # 如果是None或空字符串，设为None
            if json_value is None or (isinstance(json_value, str) and not json_value.strip()):
                processed_data[json_field] = None
                continue
            
            # 如果已经是字典对象，保持不变
            if isinstance(json_value, dict):
                continue
            
            # 尝试解析JSON字符串
            if isinstance(json_value, str):
                try:
                    import json
                    processed_data[json_field] = json.loads(json_value)
                except (ValueError, json.JSONDecodeError):
                    processed_data[json_field] = None
    
    # 确保必要字段存在并有默认值
    processed_data['version'] = int(processed_data.get('version', 1) or 1)
    processed_data['status'] = int(processed_data.get('status', 1) or 1)
    
    # 处理日期字段(如果是字符串格式)
    if 'create_time' in processed_data:
        date_value = processed_data['create_time']
        
        # 如果是None或空字符串，设为当前时间
        if date_value is None or (isinstance(date_value, str) and not date_value.strip()):
            processed_data['create_time'] = datetime.now()
        elif isinstance(date_value, str):
            try:
                # 尝试ISO格式
                processed_data['create_time'] = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                try:
                    # 尝试标准MySQL格式
                    processed_data['create_time'] = datetime.strptime(date_value, '%Y-%m-%d %H:%M:%S')
                except (ValueError, AttributeError):
                    processed_data['create_time'] = datetime.now()
    
    try:
        # 创建TickerStrategy模型实例
        return TickerStrategy(**processed_data)
    except Exception as e:
        print(f"无法创建TickerStrategy模型: {e}")
        print(f"数据: {processed_data}")
        
        # 返回带有最小必要字段的TickerStrategy（用于错误恢复）
        return TickerStrategy(
            id=processed_data.get('id', 0),
            ticker_id=processed_data.get('ticker_id', 0),
            strategy_key=processed_data.get('strategy_key', ''),
            kl_type=processed_data.get('kl_type', ''),
            time_key=processed_data.get('time_key', ''),
            status=1
        )
