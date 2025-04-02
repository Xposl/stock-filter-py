#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, Field, ConfigDict

class TickerBase(BaseModel):
    """Ticker基础模型，包含共有字段"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    group_id: int = Field(default=0, description="组ID")
    type: Optional[int] = Field(default=1, description="类型")
    source: Optional[int] = Field(default=1, description="数据来源")
    status: Optional[int] = Field(default=1, description="状态")
    is_deleted: Optional[bool] = Field(default=False, description="是否删除")
    remark: Optional[str] = Field(default=None, description="备注信息")
    
    # K线相关字段
    time_key: Optional[str] = Field(default=None, description="时间键")
    open: Optional[float] = Field(default=None, description="开盘价")
    close: Optional[float] = Field(default=None, description="收盘价")
    high: Optional[float] = Field(default=None, description="最高价")
    low: Optional[float] = Field(default=None, description="最低价")
    volume: Optional[float] = Field(default=None, description="成交量")
    turnover: Optional[float] = Field(default=None, description="成交额")
    turnover_rate: Optional[float] = Field(default=None, description="换手率")
    
    # 日期相关字段
    update_date: Optional[datetime] = Field(default=None, description="更新日期")
    listed_date: Optional[datetime] = Field(default=None, description="上市日期")
    
    model_config = ConfigDict(from_attributes=True)

class TickerCreate(TickerBase):
    """用于创建Ticker的模型"""
    pass

class TickerUpdate(BaseModel):
    """用于更新Ticker的模型，所有字段都是可选的"""
    name: Optional[str] = Field(default=None, description="股票名称")
    group_id: Optional[int] = Field(default=None, description="组ID")
    type: Optional[int] = Field(default=None, description="类型")
    source: Optional[int] = Field(default=None, description="数据来源")
    status: Optional[int] = Field(default=None, description="状态")
    is_deleted: Optional[bool] = Field(default=None, description="是否删除")
    remark: Optional[str] = Field(default=None, description="备注信息")
    
    # K线相关字段
    time_key: Optional[str] = Field(default=None, description="时间键")
    open: Optional[float] = Field(default=None, description="开盘价")
    close: Optional[float] = Field(default=None, description="收盘价")
    high: Optional[float] = Field(default=None, description="最高价")
    low: Optional[float] = Field(default=None, description="最低价")
    volume: Optional[float] = Field(default=None, description="成交量")
    turnover: Optional[float] = Field(default=None, description="成交额")
    turnover_rate: Optional[float] = Field(default=None, description="换手率")
    
    # 日期相关字段
    update_date: Optional[datetime] = Field(default=None, description="更新日期")
    listed_date: Optional[datetime] = Field(default=None, description="上市日期")
    
    model_config = ConfigDict(from_attributes=True)

class Ticker(TickerBase):
    """完整的Ticker模型，包含ID"""
    id: int = Field(..., description="ID")
    create_time: Optional[datetime] = Field(default_factory=datetime.now, description="创建时间")
    version: Optional[int] = Field(default=1, description="版本号")
    
    model_config = ConfigDict(from_attributes=True)

# 用于序列化和反序列化的辅助函数
def ticker_to_dict(ticker: Union[Ticker, TickerCreate, TickerUpdate]) -> dict:
    """
    将Ticker模型转换为字典，用于数据库操作
    
    Args:
        ticker: Ticker、TickerCreate或TickerUpdate模型
    
    Returns:
        字典表示
    """
    if isinstance(ticker, (TickerCreate, TickerUpdate)):
        return ticker.model_dump(exclude_unset=True, exclude_none=True)
    else:
        return ticker.model_dump(exclude_none=True)

def dict_to_ticker(data: dict) -> Ticker:
    """
    将字典转换为Ticker模型，处理各种数据类型转换和默认值
    
    Args:
        data: 来自数据库的字典数据
    
    Returns:
        Ticker模型实例
    """
    # 创建数据的副本，避免修改原始数据
    processed_data = data.copy()
    
    # 确保必要字段存在并有默认值
    processed_data['group_id'] = int(processed_data.get('group_id', 0) or 0)
    processed_data['type'] = int(processed_data.get('type', 1) or 1)
    processed_data['source'] = int(processed_data.get('source', 1) or 1)
    processed_data['status'] = int(processed_data.get('status', 1) or 1)
    processed_data['version'] = int(processed_data.get('version', 1) or 1)
    
    # 处理is_deleted字段，确保是布尔值
    is_deleted = processed_data.get('is_deleted', 0)
    processed_data['is_deleted'] = bool(1 if is_deleted in (1, '1', True, 'true', 'True') else 0)
    
    # 处理日期字段(如果是字符串格式)
    for date_field in ['update_date', 'listed_date', 'create_time']:
        if date_field in processed_data:
            date_value = processed_data[date_field]
            
            # 如果是None或空字符串，设为None
            if date_value is None or (isinstance(date_value, str) and not date_value.strip()):
                processed_data[date_field] = None
                continue
            
            # 如果已经是datetime对象，保持不变
            if isinstance(date_value, datetime):
                continue
            
            # 尝试将字符串转换为datetime
            if isinstance(date_value, str):
                try:
                    # 尝试ISO格式
                    processed_data[date_field] = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    try:
                        # 尝试标准MySQL格式
                        processed_data[date_field] = datetime.strptime(date_value, '%Y-%m-%d %H:%M:%S')
                    except (ValueError, AttributeError):
                        try:
                            # 尝试日期格式
                            processed_data[date_field] = datetime.strptime(date_value, '%Y-%m-%d')
                        except (ValueError, AttributeError):
                            processed_data[date_field] = None
    
    # 处理数值字段，确保是正确的类型
    for float_field in ['open', 'close', 'high', 'low', 'volume', 'turnover', 'turnover_rate']:
        if float_field in processed_data and processed_data[float_field] is not None:
            try:
                processed_data[float_field] = float(processed_data[float_field])
            except (ValueError, TypeError):
                processed_data[float_field] = None
    
    try:
        # 创建Ticker模型实例
        return Ticker(**processed_data)
    except Exception as e:
        print(f"无法创建Ticker模型: {e}")
        print(f"数据: {processed_data}")
        
        # 返回带有最小必要字段的Ticker（用于错误恢复）
        return Ticker(
            id=processed_data.get('id', 0),
            code=processed_data.get('code', 'unknown'),
            name=processed_data.get('name', 'Unknown'),
            group_id=0,
            type=1,
            status=1,
            is_deleted=False
        )
