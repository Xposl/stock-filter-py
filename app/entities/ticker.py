"""
股票实体类
定义股票的数据结构和业务逻辑
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, ClassVar

from pydantic import BaseModel, Field, field_validator


class TickerStatus(str, Enum):
    """股票状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"


class TickerType(int, Enum):
    """股票类型枚举 - 对应core/enum/ticker_type.py"""
    DEL = 0  # 无效
    STOCK = 1  # 正股
    IDX = 2  # 指数
    BOND = 3  # 债券
    DRVT = 4  # 期权
    FUTURE = 5  # 期货
    ETF = 11  # 信托,基金
    BWRT = 50  # 一揽子权证
    WARRANT = 60  # 窝轮
    PLATE = 90  # 板块
    PLATESET = 91  # 板块集


class TickerGroup(int, Enum):
    """股票组别枚举 - 对应core/enum/ticker_group.py"""
    HK = 1  # 港股
    ZH = 2  # A股
    US = 3  # 美股


class Ticker(BaseModel):
    """
    股票实体类: 定义股票的基本信息和元数据
    """
    
    # 数据库表定义
    TABLE_NAME: ClassVar[str] = "tickers"
    TABLE_SCHEMA: ClassVar[str] = """
    CREATE TABLE IF NOT EXISTS tickers (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        code VARCHAR(20) NOT NULL COMMENT '股票代码，必须包含市场前缀，格式：A股(SH.600000/SZ.000001)、港股(HK.00700)、美股(US.AAPL)',
        name VARCHAR(100) NOT NULL COMMENT '股票名称',
        type INT DEFAULT 1 COMMENT '股票类型，对应ticker_type枚举',
        market_id INT DEFAULT 0 COMMENT '市场ID，关联markets表',
        source INT DEFAULT 1 COMMENT '数据来源',
        status ENUM('active', 'inactive', 'deleted') DEFAULT 'active' COMMENT '股票状态',
        is_deleted BOOLEAN DEFAULT FALSE COMMENT '是否删除',
        remark TEXT COMMENT '备注信息',
        
        -- 估值指标
        pe_forecast DECIMAL(10,4) COMMENT '预测市盈率',
        pettm DECIMAL(10,4) COMMENT '市盈率',
        pb DECIMAL(10,4) COMMENT '市净率',
        total_share DECIMAL(20,4) COMMENT '总股本',
        lot_size INT DEFAULT 100 COMMENT '每手股数',
        
        -- 日期相关字段
        update_date TIMESTAMP NULL COMMENT '更新日期',
        listed_date DATE NULL COMMENT '上市日期',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        
        INDEX idx_code (code),
        INDEX idx_name (name),
        INDEX idx_type (type),
        INDEX idx_market_id (market_id),
        INDEX idx_status (status),
        INDEX idx_is_deleted (is_deleted),
        INDEX idx_created_at (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票信息表'
    """
    
    id: Optional[int] = Field(None, description="股票ID")
    code: str = Field(..., min_length=1, max_length=20, description="股票代码")
    name: str = Field(..., min_length=1, max_length=100, description="股票名称")
    type: TickerType = Field(TickerType.STOCK, description="股票类型")
    market_id: int = Field(default=0, description="市场ID，关联markets表")
    source: int = Field(default=1, description="数据来源")
    status: TickerStatus = Field(TickerStatus.ACTIVE, description="股票状态")
    is_deleted: bool = Field(default=False, description="是否删除")
    remark: Optional[str] = Field(None, description="备注信息")
    
    # 估值指标
    pe_forecast: Optional[float] = Field(None, description="预测市盈率")
    pettm: Optional[float] = Field(None, description="市盈率")
    pb: Optional[float] = Field(None, description="市净率")
    total_share: Optional[float] = Field(None, description="总股本")
    lot_size: int = Field(default=100, description="每手股数")
    
    # 日期相关字段
    update_date: Optional[datetime] = Field(None, description="更新日期")
    listed_date: Optional[datetime] = Field(None, description="上市日期")
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
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        """验证股票代码格式"""
        if not v or not v.strip():
            raise ValueError("股票代码不能为空")
        
        # 验证市场前缀格式
        valid_prefixes = ['SH.', 'SZ.', 'HK.', 'US.']
        if not any(v.startswith(prefix) for prefix in valid_prefixes):
            raise ValueError(f"股票代码格式错误，必须以以下前缀开头: {', '.join(valid_prefixes)}")
        
        return v.strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "type": self.type.value,
            "market_id": self.market_id,
            "source": self.source,
            "status": self.status.value,
            "is_deleted": self.is_deleted,
            "remark": self.remark,
            "pe_forecast": self.pe_forecast,
            "pettm": self.pettm,
            "pb": self.pb,
            "total_share": self.total_share,
            "lot_size": self.lot_size,
            "update_date": self.update_date.isoformat() if self.update_date else None,
            "listed_date": self.listed_date.isoformat() if self.listed_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Ticker":
        """从字典创建实例"""
        # 处理日期时间字段
        for date_field in ["update_date", "listed_date", "created_at", "updated_at"]:
            if isinstance(data.get(date_field), str):
                try:
                    data[date_field] = datetime.fromisoformat(data[date_field])
                except ValueError:
                    data[date_field] = None
        
        # 处理枚举字段 - 转换字符串为枚举对象
        if "type" in data and isinstance(data["type"], (int, str)):
            try:
                data["type"] = TickerType(int(data["type"]))
            except ValueError:
                data["type"] = TickerType.STOCK
        
        if "status" in data and isinstance(data["status"], str):
            try:
                data["status"] = TickerStatus(data["status"])
            except ValueError:
                data["status"] = TickerStatus.ACTIVE
        
        return cls(**data)
    
    def is_active(self) -> bool:
        """检查股票是否处于活跃状态"""
        return self.status == TickerStatus.ACTIVE and not self.is_deleted
    
    def get_market_prefix(self) -> str:
        """获取市场前缀"""
        if self.code.startswith('SH.'):
            return 'SH'
        elif self.code.startswith('SZ.'):
            return 'SZ'
        elif self.code.startswith('HK.'):
            return 'HK'
        elif self.code.startswith('US.'):
            return 'US'
        else:
            return 'UNKNOWN'
    
    def get_group_id_by_code(self) -> int:
        """根据股票代码获取组别ID"""
        if self.code.startswith('HK.'):
            return TickerGroup.HK.value
        elif self.code.startswith('US.'):
            return TickerGroup.US.value
        elif self.code.startswith('SZ.') or self.code.startswith('SH.'):
            return TickerGroup.ZH.value
        else:
            return TickerGroup.ZH.value  # 默认A股


class TickerCreate(BaseModel):
    """创建股票的请求模型"""
    code: str = Field(..., min_length=1, max_length=20, description="股票代码")
    name: str = Field(..., min_length=1, max_length=100, description="股票名称")
    type: int = Field(TickerType.STOCK.value, description="股票类型")
    market_id: int = Field(default=0, description="市场ID，关联markets表")
    source: int = Field(default=1, description="数据来源")
    status: str = Field(TickerStatus.ACTIVE.value, description="股票状态")
    is_deleted: bool = Field(default=False, description="是否删除")
    remark: Optional[str] = Field(None, description="备注信息")
    pe_forecast: Optional[float] = Field(None, description="预测市盈率")
    pettm: Optional[float] = Field(None, description="市盈率")
    pb: Optional[float] = Field(None, description="市净率")
    total_share: Optional[float] = Field(None, description="总股本")
    lot_size: int = Field(default=100, description="每手股数")
    update_date: Optional[datetime] = Field(None, description="更新日期")
    listed_date: Optional[datetime] = Field(None, description="上市日期")

    model_config = {"from_attributes": True, "populate_by_name": True}

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        """验证股票类型"""
        try:
            valid_values = [t.value for t in TickerType]
            if v not in valid_values:
                raise ValueError(f"无效的股票类型: {v}。有效值为: {valid_values}")
            return v
        except Exception as e:
            raise ValueError(f"验证股票类型失败: {e}")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """验证股票状态"""
        try:
            valid_values = [s.value for s in TickerStatus]
            if v not in valid_values:
                raise ValueError(f"无效的股票状态: {v}。有效值为: {valid_values}")
            return v
        except Exception as e:
            raise ValueError(f"验证股票状态失败: {e}")


class TickerUpdate(BaseModel):
    """更新股票的请求模型"""
    code: Optional[str] = Field(None, min_length=1, max_length=20, description="股票代码")
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="股票名称")
    type: Optional[int] = Field(None, description="股票类型")
    market_id: Optional[int] = Field(None, description="市场ID，关联markets表")
    source: Optional[int] = Field(None, description="数据来源")
    status: Optional[str] = Field(None, description="股票状态")
    is_deleted: Optional[bool] = Field(None, description="是否删除")
    remark: Optional[str] = Field(None, description="备注信息")
    pe_forecast: Optional[float] = Field(None, description="预测市盈率")
    pettm: Optional[float] = Field(None, description="市盈率")
    pb: Optional[float] = Field(None, description="市净率")
    total_share: Optional[float] = Field(None, description="总股本")
    lot_size: Optional[int] = Field(None, description="每手股数")
    update_date: Optional[datetime] = Field(None, description="更新日期")
    listed_date: Optional[datetime] = Field(None, description="上市日期")


class TickerDTO(BaseModel):
    """股票响应模型"""
    id: int = Field(..., description="股票ID")
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    type: TickerType = Field(..., description="股票类型")
    market_id: int = Field(..., description="市场ID")
    source: int = Field(..., description="数据来源")
    status: TickerStatus = Field(..., description="股票状态")
    is_deleted: bool = Field(..., description="是否删除")
    remark: Optional[str] = Field(None, description="备注信息")
    pe_forecast: Optional[float] = Field(None, description="预测市盈率")
    pettm: Optional[float] = Field(None, description="市盈率")
    pb: Optional[float] = Field(None, description="市净率")
    total_share: Optional[float] = Field(None, description="总股本")
    lot_size: int = Field(..., description="每手股数")
    update_date: Optional[datetime] = Field(None, description="更新日期")
    listed_date: Optional[datetime] = Field(None, description="上市日期")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # Pydantic v2 配置
    model_config = {"from_attributes": True, "populate_by_name": True}

    @classmethod
    def from_entity(cls, ticker: Ticker) -> "TickerDTO":
        """从实体对象创建响应模型"""
        return cls(
            id=ticker.id,
            code=ticker.code,
            name=ticker.name,
            type=ticker.type,
            market_id=ticker.market_id,
            source=ticker.source,
            status=ticker.status,
            is_deleted=ticker.is_deleted,
            remark=ticker.remark,
            pe_forecast=ticker.pe_forecast,
            pettm=ticker.pettm,
            pb=ticker.pb,
            total_share=ticker.total_share,
            lot_size=ticker.lot_size,
            update_date=ticker.update_date,
            listed_date=ticker.listed_date,
            created_at=ticker.created_at,
            updated_at=ticker.updated_at
        ) 