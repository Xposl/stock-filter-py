from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class TickerBase(BaseModel):
    code: str
    name: str
    group_id: int = 0
    type: Optional[int] = 1
    source: Optional[int] = 1
    status: Optional[int] = 1
    is_deleted: Optional[bool] = False
    
    # K线相关字段
    time_key: Optional[str] = None
    open: Optional[float] = None
    close: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    volume: Optional[float] = None
    turnover: Optional[float] = None
    turnover_rate: Optional[float] = None
    
    # 日期相关字段
    update_date: Optional[datetime] = None
    listed_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)  # 更新配置方式

class TickerCreate(TickerBase):
    pass

class TickerUpdate(BaseModel):
    name: Optional[str] = None
    group_id: Optional[int] = None
    status: Optional[int] = None
    type: Optional[int] = None
    source: Optional[int] = None
    is_deleted: Optional[bool] = None

class Ticker(TickerBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)
