#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Optional, Union, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict

class TickerValuationBase(BaseModel):
    """估值基础模型，包含共有字段"""
    ticker_id: int = Field(..., description="股票ID")
    valuation_key: str = Field(..., description="估值键，使用Valuation的getKey值")
    time_key: str = Field(..., description="时间键")
    target_price: Optional[float] = Field(default=-1, description="平均目标价")
    max_target_price: Optional[float] = Field(default=-1, description="最高目标价")
    min_target_price: Optional[float] = Field(default=-1, description="最低目标价")
    remark: Optional[str] = Field(default=None, description="备注")
    status: Optional[int] = Field(default=1, description="状态")
    
    model_config = ConfigDict(from_attributes=True)

class TickerValuationCreate(TickerValuationBase):
    """用于创建估值的模型"""
    pass

class TickerValuationUpdate(BaseModel):
    """用于更新估值的模型，所有字段都是可选的"""
    time_key: Optional[str] = Field(default=None, description="时间键")
    target_price: Optional[float] = Field(default=None, description="平均目标价")
    max_target_price: Optional[float] = Field(default=None, description="最高目标价")
    min_target_price: Optional[float] = Field(default=None, description="最低目标价")
    remark: Optional[str] = Field(default=None, description="备注")
    status: Optional[int] = Field(default=None, description="状态")
    
    model_config = ConfigDict(from_attributes=True)

class TickerValuation(TickerValuationBase):
    """完整的估值模型，包含ID"""
    id: int = Field(..., description="ID")
    code: Optional[str] = Field(default=None, description="代码")
    version: Optional[int] = Field(default=1, description="版本号")
    create_time: Optional[datetime] = Field(default_factory=datetime.now, description="创建时间")
    
    model_config = ConfigDict(from_attributes=True)

# 用于序列化和反序列化的辅助函数
def ticker_valuation_to_dict(valuation: Union[TickerValuation, TickerValuationCreate, TickerValuationUpdate]) -> dict:
    """
    将TickerValuation模型转换为字典，用于数据库操作
    
    Args:
        valuation: TickerValuation、TickerValuationCreate或TickerValuationUpdate模型
    
    Returns:
        字典表示
    """
    result = {}
    
    if isinstance(valuation, (TickerValuationCreate, TickerValuationUpdate)):
        result = valuation.model_dump(exclude_unset=True, exclude_none=True)
    else:
        result = valuation.model_dump(exclude_none=True)
        
    return result

def dict_to_ticker_valuation(data: dict) -> TickerValuation:
    """
    将字典转换为TickerValuation模型，处理各种数据类型转换和默认值
    
    Args:
        data: 来自数据库的字典数据
    
    Returns:
        TickerValuation模型实例
    """
    # 创建数据的副本，避免修改原始数据
    processed_data = data.copy()
    
    # 确保必要字段存在并有默认值
    for field in ['target_price', 'max_target_price', 'min_target_price']:
        if field in processed_data:
            try:
                value = processed_data[field]
                processed_data[field] = float(value) if value is not None else -1
            except (ValueError, TypeError):
                processed_data[field] = -1
    
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
        # 创建TickerValuation模型实例
        return TickerValuation(**processed_data)
    except Exception as e:
        print(f"无法创建TickerValuation模型: {e}")
        print(f"数据: {processed_data}")
        
        # 返回带有最小必要字段的TickerValuation（用于错误恢复）
        return TickerValuation(
            id=processed_data.get('id', 0),
            ticker_id=processed_data.get('ticker_id', 0),
            valuation_key=processed_data.get('valuation_key', ''),
            time_key=processed_data.get('time_key', ''),
            target_price=-1,
            max_target_price=-1,
            min_target_price=-1,
            status=1
        )
