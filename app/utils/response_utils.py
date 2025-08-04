"""
统一响应格式工具
提供标准化的API响应格式，确保Swagger文档生成完整的schema
符合PRD.md第8.6节统一响应格式要求
"""

import uuid
from typing import Any, Dict, Optional, List, Generic, TypeVar, Union
from datetime import datetime

from pydantic import BaseModel, Field

# 移除Agent相关导入，因为当前项目主要关注股票功能

# 泛型类型定义
DataType = TypeVar('DataType')

# ================== 基础响应模型 ==================

class ErrorDetails(BaseModel):
    """错误详情模型"""
    type: str = Field(..., description="错误类型")
    details: str = Field(..., description="错误详细信息")

class PaginationInfo(BaseModel):
    """分页信息模型"""
    page: int = Field(..., description="当前页码", ge=1)
    page_size: int = Field(..., description="每页数量", ge=1)
    total: int = Field(..., description="总记录数", ge=0)
    total_pages: int = Field(..., description="总页数", ge=0)

class BaseResponse(BaseModel, Generic[DataType]):
    """基础响应模型"""
    success: bool = Field(..., description="操作是否成功")
    code: int = Field(..., description="响应状态码")
    message: str = Field(..., description="响应消息")
    timestamp: str = Field(..., description="响应时间戳")
    request_id: str = Field(..., description="请求ID")

class SuccessResponse(BaseResponse[DataType]):
    """成功响应模型"""
    success: bool = Field(True, description="操作成功标识")
    data: Optional[DataType] = Field(None, description="响应数据")

class ErrorResponse(BaseResponse[None]):
    """错误响应模型"""
    success: bool = Field(False, description="操作失败标识")
    error: ErrorDetails = Field(..., description="错误信息")

# ================== 特定响应类型 ==================

# 通用数据响应
class PaginatedData(BaseModel, Generic[DataType]):
    items: List[DataType] = Field(..., description="消息列表")
    pagination: PaginationInfo = Field(..., description="分页信息")

class HealthCheckDataResponse(BaseModel):
    """健康检查数据响应"""
    status: str = Field(..., description="服务状态")
    service: str = Field(..., description="服务名称")
    handlers: Optional[Dict[str, str]] = Field(None, description="处理器状态")
    version: Optional[str] = Field(None, description="版本信息")

class SearchResultDataResponse(BaseModel):
    """搜索结果数据响应"""
    items: List[Dict[str, Any]] = Field(..., description="搜索结果列表")
    pagination: PaginationInfo = Field(..., description="分页信息")
    search: Dict[str, Any] = Field(..., description="搜索条件")
    conversation: Dict[str, str] = Field(..., description="对话信息")

# ================== 具体响应类型定义 ==================

# 消息相关响应
SearchResultSuccessResponse = SuccessResponse[SearchResultDataResponse]

# 健康检查响应
HealthCheckSuccessResponse = SuccessResponse[HealthCheckDataResponse]

# 通用响应
GenericSuccessResponse = SuccessResponse[Dict[str, Any]]

# ================== 工具函数 ==================

def create_success_response(
    data: Any = None,
    message: str = "操作成功",
    code: int = 200
) -> Dict[str, Any]:
    """
    创建成功响应
    
    Args:
        data: 响应数据
        message: 响应消息
        code: 状态码
        
    Returns:
        标准成功响应字典
    """
    return {
        "success": True,
        "code": code,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat(),
        "request_id": str(uuid.uuid4())
    }

def create_error_response(
    message: str,
    code: int = 400,
    error_type: str = "ValidationError",
    details: Optional[str] = None
) -> Dict[str, Any]:
    """
    创建错误响应
    
    Args:
        message: 错误消息
        code: 状态码
        error_type: 错误类型
        details: 错误详情
        
    Returns:
        标准错误响应字典
    """
    return {
        "success": False,
        "code": code,
        "message": message,
        "error": {
            "type": error_type,
            "details": details or message
        },
        "timestamp": datetime.now().isoformat(),
        "request_id": str(uuid.uuid4())
    }

def create_paginated_response(
    items: List[Any],
    total: int,
    page: int,
    page_size: int,
    message: str = "获取数据成功",
    extra_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    创建分页响应
    
    Args:
        items: 数据列表
        total: 总记录数
        page: 当前页码
        page_size: 每页数量
        message: 响应消息
        extra_data: 额外数据
        
    Returns:
        标准分页响应字典
    """
    total_pages = (total + page_size - 1) // page_size
    
    data = {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages
        }
    }
    
    # 合并额外数据
    if extra_data:
        data.update(extra_data)
    
    return create_success_response(
        data=data,
        message=message
    )

# ================== 响应模型映射 ==================

def get_response_model(response_type: str) -> type:
    """
    根据响应类型获取对应的Pydantic模型
    
    Args:
        response_type: 响应类型标识
        
    Returns:
        对应的Pydantic响应模型类
    """
    response_models = {
        "search_result": SearchResultSuccessResponse,
        "health": HealthCheckSuccessResponse,
        "error": ErrorResponse
    }
    
    return response_models.get(response_type, GenericSuccessResponse) 