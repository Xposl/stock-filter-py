"""
股票估值实体类
定义股票估值的数据结构和业务逻辑
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, ClassVar

from pydantic import BaseModel, Field, field_validator


class ValuationStatus(int, Enum):
    """估值状态枚举"""
    ACTIVE = 1      # 活跃
    INACTIVE = 0    # 非活跃
    DELETED = -1    # 已删除


class TickerValuation(BaseModel):
    """
    股票估值实体类: 定义股票估值的基本信息和元数据
    """
    
    # 数据库表定义
    TABLE_NAME: ClassVar[str] = "ticker_valuations"
    TABLE_SCHEMA: ClassVar[str] = """
    CREATE TABLE IF NOT EXISTS ticker_valuations (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        ticker_id INT NOT NULL COMMENT '股票ID',
        valuation_key VARCHAR(100) NOT NULL COMMENT '估值键，使用Valuation的getKey值',
        time_key VARCHAR(50) NOT NULL COMMENT '时间键',
        target_price DECIMAL(10,4) DEFAULT -1 COMMENT '平均目标价',
        max_target_price DECIMAL(10,4) DEFAULT -1 COMMENT '最高目标价',
        min_target_price DECIMAL(10,4) DEFAULT -1 COMMENT '最低目标价',
        remark TEXT COMMENT '备注',
        status INT DEFAULT 1 COMMENT '状态：1-活跃，0-非活跃，-1-已删除',
        code VARCHAR(50) COMMENT '代码',
        version INT DEFAULT 1 COMMENT '版本号',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        
        INDEX idx_ticker_id (ticker_id),
        INDEX idx_valuation_key (valuation_key),
        INDEX idx_time_key (time_key),
        INDEX idx_target_price (target_price),
        INDEX idx_status (status),
        INDEX idx_code (code),
        INDEX idx_created_at (created_at),
        UNIQUE KEY uk_ticker_valuation (ticker_id, valuation_key)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票估值表'
    """
    
    id: Optional[int] = Field(None, description="估值ID")
    ticker_id: int = Field(..., description="股票ID")
    valuation_key: str = Field(..., min_length=1, max_length=100, description="估值键，使用Valuation的getKey值")
    time_key: str = Field(..., min_length=1, max_length=50, description="时间键")
    target_price: Optional[float] = Field(default=-1, description="平均目标价")
    max_target_price: Optional[float] = Field(default=-1, description="最高目标价")
    min_target_price: Optional[float] = Field(default=-1, description="最低目标价")
    remark: Optional[str] = Field(None, description="备注")
    status: ValuationStatus = Field(ValuationStatus.ACTIVE, description="状态")
    code: Optional[str] = Field(None, max_length=50, description="代码")
    version: int = Field(default=1, description="版本号")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    
    # Pydantic v2 配置
    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "json_encoders": {
            datetime: lambda dt: dt.isoformat() if dt else None
        }
    }
    
    @field_validator('valuation_key')
    @classmethod
    def validate_valuation_key(cls, v):
        """验证估值键"""
        if not v or not v.strip():
            raise ValueError("估值键不能为空")
        
        # 验证估值键格式（只允许字母、数字、下划线）
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError("估值键只能包含字母、数字和下划线")
        
        return v.strip()
    
    @field_validator('time_key')
    @classmethod
    def validate_time_key(cls, v):
        """验证时间键"""
        if not v or not v.strip():
            raise ValueError("时间键不能为空")
        
        return v.strip()
    
    @field_validator('target_price', 'max_target_price', 'min_target_price')
    @classmethod
    def validate_price(cls, v):
        """验证价格字段"""
        if v is not None and v < -1:
            raise ValueError("价格不能小于-1")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "ticker_id": self.ticker_id,
            "valuation_key": self.valuation_key,
            "time_key": self.time_key,
            "target_price": self.target_price,
            "max_target_price": self.max_target_price,
            "min_target_price": self.min_target_price,
            "remark": self.remark,
            "status": self.status.value,
            "code": self.code,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TickerValuation":
        """从字典创建实例"""
        # 处理日期时间字段
        for date_field in ["created_at", "updated_at"]:
            if isinstance(data.get(date_field), str):
                try:
                    data[date_field] = datetime.fromisoformat(data[date_field])
                except ValueError:
                    data[date_field] = None
        
        # 处理枚举字段 - 转换整数为枚举对象
        if "status" in data and isinstance(data["status"], int):
            try:
                data["status"] = ValuationStatus(data["status"])
            except ValueError:
                data["status"] = ValuationStatus.ACTIVE
        
        return cls(**data)
    
    def is_active(self) -> bool:
        """检查估值是否处于活跃状态"""
        return self.status == ValuationStatus.ACTIVE
    
    def is_deleted(self) -> bool:
        """检查估值是否已删除"""
        return self.status == ValuationStatus.DELETED
    
    def get_unique_key(self) -> str:
        """获取唯一键（用于去重）"""
        return f"{self.ticker_id}_{self.valuation_key}"
    
    def has_valid_target_price(self) -> bool:
        """检查是否有有效的目标价"""
        return self.target_price is not None and self.target_price > 0
    
    def has_valid_price_range(self) -> bool:
        """检查是否有有效的价格范围"""
        return (
            self.max_target_price is not None and self.max_target_price > 0 and
            self.min_target_price is not None and self.min_target_price > 0 and
            self.max_target_price >= self.min_target_price
        )
    
    def get_price_range(self) -> Optional[Dict[str, float]]:
        """获取价格范围"""
        if not self.has_valid_price_range():
            return None
        
        return {
            "min": self.min_target_price,
            "max": self.max_target_price,
            "avg": self.target_price
        }
    
    def get_valuation_confidence(self) -> str:
        """获取估值置信度"""
        if not self.has_valid_target_price():
            return "无数据"
        
        if self.has_valid_price_range():
            price_range = self.max_target_price - self.min_target_price
            avg_price = self.target_price
            
            if avg_price > 0:
                confidence_ratio = price_range / avg_price
                
                if confidence_ratio <= 0.1:
                    return "高"
                elif confidence_ratio <= 0.2:
                    return "中"
                else:
                    return "低"
        
        return "未知"
    
    def get_valuation_trend(self, current_price: float) -> str:
        """获取估值趋势"""
        if not self.has_valid_target_price() or current_price <= 0:
            return "未知"
        
        target_ratio = self.target_price / current_price
        
        if target_ratio >= 1.2:
            return "强烈看涨"
        elif target_ratio >= 1.1:
            return "看涨"
        elif target_ratio >= 0.9:
            return "中性"
        elif target_ratio >= 0.8:
            return "看跌"
        else:
            return "强烈看跌"


class TickerValuationCreate(BaseModel):
    """创建股票估值的请求模型"""
    ticker_id: int = Field(..., description="股票ID")
    valuation_key: str = Field(..., min_length=1, max_length=100, description="估值键，使用Valuation的getKey值")
    time_key: str = Field(..., min_length=1, max_length=50, description="时间键")
    target_price: Optional[float] = Field(default=-1, description="平均目标价")
    max_target_price: Optional[float] = Field(default=-1, description="最高目标价")
    min_target_price: Optional[float] = Field(default=-1, description="最低目标价")
    remark: Optional[str] = Field(None, description="备注")
    status: int = Field(ValuationStatus.ACTIVE.value, description="状态")
    code: Optional[str] = Field(None, max_length=50, description="代码")
    version: int = Field(default=1, description="版本号")

    model_config = {"from_attributes": True, "populate_by_name": True}

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """验证状态"""
        try:
            valid_values = [s.value for s in ValuationStatus]
            if v not in valid_values:
                raise ValueError(f"无效的状态: {v}。有效值为: {valid_values}")
            return v
        except Exception as e:
            raise ValueError(f"验证状态失败: {e}")


class TickerValuationUpdate(BaseModel):
    """更新股票估值的请求模型"""
    time_key: Optional[str] = Field(None, min_length=1, max_length=50, description="时间键")
    target_price: Optional[float] = Field(None, description="平均目标价")
    max_target_price: Optional[float] = Field(None, description="最高目标价")
    min_target_price: Optional[float] = Field(None, description="最低目标价")
    remark: Optional[str] = Field(None, description="备注")
    status: Optional[int] = Field(None, description="状态")
    code: Optional[str] = Field(None, max_length=50, description="代码")
    version: Optional[int] = Field(None, description="版本号")


class TickerValuationDTO(BaseModel):
    """股票估值响应模型"""
    id: int = Field(..., description="估值ID")
    ticker_id: int = Field(..., description="股票ID")
    valuation_key: str = Field(..., description="估值键，使用Valuation的getKey值")
    time_key: str = Field(..., description="时间键")
    target_price: Optional[float] = Field(None, description="平均目标价")
    max_target_price: Optional[float] = Field(None, description="最高目标价")
    min_target_price: Optional[float] = Field(None, description="最低目标价")
    remark: Optional[str] = Field(None, description="备注")
    status: ValuationStatus = Field(..., description="状态")
    code: Optional[str] = Field(None, description="代码")
    version: int = Field(..., description="版本号")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # Pydantic v2 配置
    model_config = {"from_attributes": True, "populate_by_name": True}

    @classmethod
    def from_entity(cls, valuation: TickerValuation) -> "TickerValuationDTO":
        """从实体对象创建响应模型"""
        return cls(
            id=valuation.id,
            ticker_id=valuation.ticker_id,
            valuation_key=valuation.valuation_key,
            time_key=valuation.time_key,
            target_price=valuation.target_price,
            max_target_price=valuation.max_target_price,
            min_target_price=valuation.min_target_price,
            remark=valuation.remark,
            status=valuation.status,
            code=valuation.code,
            version=valuation.version,
            created_at=valuation.created_at,
            updated_at=valuation.updated_at
        ) 