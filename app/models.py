"""
应用模型定义
包含API请求和响应的Pydantic模型
"""

from typing import Optional, List
from pydantic import BaseModel, Field

class PageRequest(BaseModel):
    """分页请求模型"""
    page: int = Field(1, description="页码", ge=1)
    page_size: int = Field(10, description="每页数量", ge=1, le=100)
    search: Optional[str] = Field(None, description="搜索关键词")
    sort: Optional[List[str]] = Field(None, description="排序字段列表")

class TickerRequest(BaseModel):
    """股票请求模型"""
    market: str = Field(..., description="市场代码")
    ticker_code: str = Field(..., description="股票代码")
    days: Optional[int] = Field(600, description="K线数据天数", ge=1, le=1000) 