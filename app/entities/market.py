"""
市场实体类
定义市场的数据结构和业务逻辑
"""

from datetime import datetime, time
from enum import Enum
from typing import Dict, Any, Optional, ClassVar, List

from pydantic import BaseModel, Field, field_validator


class MarketStatus(str, Enum):
    """市场状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class Market(BaseModel):
    """
    市场实体类: 定义市场的基本信息和交易规则
    """
    
    # 数据库表定义
    TABLE_NAME: ClassVar[str] = "markets"
    TABLE_SCHEMA: ClassVar[str] = """
    CREATE TABLE IF NOT EXISTS markets (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        code VARCHAR(10) NOT NULL UNIQUE COMMENT '市场代码',
        name VARCHAR(100) NOT NULL COMMENT '市场名称',
        region VARCHAR(50) NOT NULL COMMENT '地区',
        currency VARCHAR(10) DEFAULT 'USD' COMMENT '货币代码',
        timezone VARCHAR(50) NOT NULL COMMENT '时区，如 Asia/Shanghai',
        open_time TIME NOT NULL COMMENT '开盘时间',
        close_time TIME NOT NULL COMMENT '收盘时间',
        trading_days VARCHAR(100) DEFAULT 'Mon,Tue,Wed,Thu,Fri' COMMENT '交易日，逗号分隔',
        status ENUM('active', 'inactive', 'suspended') DEFAULT 'active' COMMENT '市场状态',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        
        INDEX idx_code (code),
        INDEX idx_name (name),
        INDEX idx_region (region),
        INDEX idx_status (status),
        INDEX idx_created_at (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='市场信息表'
    """
    
    id: Optional[int] = Field(None, description="市场ID")
    code: str = Field(..., min_length=1, max_length=10, description="市场代码")
    name: str = Field(..., min_length=1, max_length=100, description="市场名称")
    region: str = Field(..., min_length=1, max_length=50, description="地区")
    currency: str = Field(default="USD", min_length=1, max_length=10, description="货币代码")
    timezone: str = Field(..., min_length=1, max_length=50, description="时区")
    open_time: time = Field(..., description="开盘时间")
    close_time: time = Field(..., description="收盘时间")
    trading_days: str = Field(default="Mon,Tue,Wed,Thu,Fri", description="交易日，逗号分隔")
    status: MarketStatus = Field(MarketStatus.ACTIVE, description="市场状态")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    
    # Pydantic v2 配置
    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "json_encoders": {
            datetime: lambda dt: dt.isoformat() if dt else None,
            time: lambda t: t.strftime("%H:%M:%S") if t else None
        }
    }
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        """验证市场代码格式"""
        if not v or not v.strip():
            raise ValueError("市场代码不能为空")
        return v.strip().upper()
    
    @field_validator('trading_days')
    @classmethod
    def validate_trading_days(cls, v):
        """验证交易日格式"""
        if not v:
            return "Mon,Tue,Wed,Thu,Fri"
        
        valid_days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        days = [day.strip() for day in v.split(",") if day.strip()]
        
        for day in days:
            if day not in valid_days:
                raise ValueError(f"无效的交易日: {day}。有效值为: {', '.join(valid_days)}")
        
        return ",".join(days)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "region": self.region,
            "currency": self.currency,
            "timezone": self.timezone,
            "open_time": self.open_time.strftime("%H:%M:%S") if self.open_time else None,
            "close_time": self.close_time.strftime("%H:%M:%S") if self.close_time else None,
            "trading_days": self.trading_days,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Market":
        """从字典创建实例"""
        # 处理日期时间字段
        for date_field in ["created_at", "updated_at"]:
            if isinstance(data.get(date_field), str):
                try:
                    data[date_field] = datetime.fromisoformat(data[date_field])
                except ValueError:
                    data[date_field] = None
        
        # 处理时间字段
        for time_field in ["open_time", "close_time"]:
            if isinstance(data.get(time_field), str):
                try:
                    data[time_field] = datetime.strptime(data[time_field], "%H:%M:%S").time()
                except ValueError:
                    data[time_field] = None
        
        # 处理枚举字段 - 转换字符串为枚举对象
        if "status" in data and isinstance(data["status"], str):
            try:
                data["status"] = MarketStatus(data["status"])
            except ValueError:
                data["status"] = MarketStatus.ACTIVE
        
        return cls(**data)
    
    def is_active(self) -> bool:
        """检查市场是否处于活跃状态"""
        return self.status == MarketStatus.ACTIVE
    
    def is_trading_day(self, weekday: int) -> bool:
        """
        检查指定星期几是否为交易日
        
        Args:
            weekday: 星期几 (0=Monday, 6=Sunday)
            
        Returns:
            是否为交易日
        """
        weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        if 0 <= weekday <= 6:
            day_name = weekday_names[weekday]
            return day_name in self.trading_days.split(",")
        return False
    
    def get_trading_days_list(self) -> List[str]:
        """
        获取交易日列表
        
        Returns:
            交易日列表，如 ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
        """
        return [day.strip() for day in self.trading_days.split(",") if day.strip()]
    
    def get_public_id(self) -> int:
        """获取对外公开的ID"""
        return self.id


class MarketCreate(BaseModel):
    """创建市场的请求模型"""
    code: str = Field(..., min_length=1, max_length=10, description="市场代码")
    name: str = Field(..., min_length=1, max_length=100, description="市场名称")
    region: str = Field(..., min_length=1, max_length=50, description="地区")
    currency: str = Field(default="USD", min_length=1, max_length=10, description="货币代码")
    timezone: str = Field(..., min_length=1, max_length=50, description="时区")
    open_time: time = Field(..., description="开盘时间")
    close_time: time = Field(..., description="收盘时间")
    trading_days: str = Field(default="Mon,Tue,Wed,Thu,Fri", description="交易日，逗号分隔")
    status: str = Field(MarketStatus.ACTIVE.value, description="市场状态")

    model_config = {"from_attributes": True, "populate_by_name": True}

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """验证市场状态"""
        try:
            valid_values = [s.value for s in MarketStatus]
            if v not in valid_values:
                raise ValueError(f"无效的市场状态: {v}。有效值为: {valid_values}")
            return v
        except Exception as e:
            raise ValueError(f"验证市场状态失败: {e}")


class MarketUpdate(BaseModel):
    """更新市场的请求模型"""
    code: Optional[str] = Field(None, min_length=1, max_length=10, description="市场代码")
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="市场名称")
    region: Optional[str] = Field(None, min_length=1, max_length=50, description="地区")
    currency: Optional[str] = Field(None, min_length=1, max_length=10, description="货币代码")
    timezone: Optional[str] = Field(None, min_length=1, max_length=50, description="时区")
    open_time: Optional[time] = Field(None, description="开盘时间")
    close_time: Optional[time] = Field(None, description="收盘时间")
    trading_days: Optional[str] = Field(None, description="交易日，逗号分隔")
    status: Optional[str] = Field(None, description="市场状态")


class MarketDTO(BaseModel):
    """市场响应模型"""
    id: int = Field(..., description="市场ID")
    code: str = Field(..., description="市场代码")
    name: str = Field(..., description="市场名称")
    region: str = Field(..., description="地区")
    currency: str = Field(..., description="货币代码")
    timezone: str = Field(..., description="时区")
    open_time: time = Field(..., description="开盘时间")
    close_time: time = Field(..., description="收盘时间")
    trading_days: str = Field(..., description="交易日，逗号分隔")
    status: MarketStatus = Field(..., description="市场状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # Pydantic v2 配置
    model_config = {"from_attributes": True, "populate_by_name": True}

    @classmethod
    def from_entity(cls, market: Market) -> "MarketDTO":
        """从实体对象创建响应模型"""
        return cls(
            id=market.id,
            code=market.code,
            name=market.name,
            region=market.region,
            currency=market.currency,
            timezone=market.timezone,
            open_time=market.open_time,
            close_time=market.close_time,
            trading_days=market.trading_days,
            status=market.status,
            created_at=market.created_at,
            updated_at=market.updated_at
        ) 