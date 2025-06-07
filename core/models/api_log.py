from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ApiLog(BaseModel):
    id: Optional[int] = Field(default=None, description="主键")
    path: str = Field(..., description="API路径")
    method: str = Field(..., description="HTTP方法")
    params: Optional[str] = Field(default=None, description="请求参数")
    exception: Optional[str] = Field(default=None, description="异常信息")
    traceback: Optional[str] = Field(default=None, description="异常堆栈")
    created_at: Optional[datetime] = Field(
        default_factory=datetime.now, description="创建时间"
    )
