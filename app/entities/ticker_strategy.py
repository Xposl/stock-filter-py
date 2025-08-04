"""
股票策略实体类
定义股票策略的数据结构和业务逻辑
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, ClassVar, List, Union

from pydantic import BaseModel, Field, field_validator


class StrategyStatus(int, Enum):
    """策略状态枚举"""
    ACTIVE = 1      # 活跃
    INACTIVE = 0    # 非活跃
    DELETED = -1    # 已删除


class TickerStrategy(BaseModel):
    """
    股票策略实体类: 定义股票策略的基本信息和元数据
    """
    
    # 数据库表定义
    TABLE_NAME: ClassVar[str] = "ticker_strategies"
    TABLE_SCHEMA: ClassVar[str] = """
    CREATE TABLE IF NOT EXISTS ticker_strategies (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        ticker_id INT NOT NULL COMMENT '股票ID',
        strategy_key VARCHAR(100) NOT NULL COMMENT '策略键，使用Strategy的getKey值',
        kl_type VARCHAR(20) NOT NULL COMMENT 'K线类型',
        time_key VARCHAR(50) NOT NULL COMMENT '时间键',
        data JSON COMMENT '策略数据',
        pos_data JSON COMMENT '持仓数据',
        status INT DEFAULT 1 COMMENT '状态：1-活跃，0-非活跃，-1-已删除',
        code VARCHAR(50) COMMENT '代码',
        version INT DEFAULT 1 COMMENT '版本号',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        
        INDEX idx_ticker_id (ticker_id),
        INDEX idx_strategy_key (strategy_key),
        INDEX idx_kl_type (kl_type),
        INDEX idx_time_key (time_key),
        INDEX idx_status (status),
        INDEX idx_code (code),
        INDEX idx_created_at (created_at),
        UNIQUE KEY uk_ticker_strategy (ticker_id, strategy_key, kl_type)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票策略表'
    """
    
    id: Optional[int] = Field(None, description="策略ID")
    ticker_id: int = Field(..., description="股票ID")
    strategy_key: str = Field(..., min_length=1, max_length=100, description="策略键，使用Strategy的getKey值")
    kl_type: str = Field(..., min_length=1, max_length=20, description="K线类型")
    time_key: str = Field(..., min_length=1, max_length=50, description="时间键")
    data: Optional[Union[List[Any], Dict[str, Any]]] = Field(None, description="策略数据")
    pos_data: Optional[Union[List[Any], Dict[str, Any]]] = Field(None, description="持仓数据")
    status: StrategyStatus = Field(StrategyStatus.ACTIVE, description="状态")
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
    
    @field_validator('strategy_key')
    @classmethod
    def validate_strategy_key(cls, v):
        """验证策略键"""
        if not v or not v.strip():
            raise ValueError("策略键不能为空")
        
        # 验证策略键格式（只允许字母、数字、下划线）
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError("策略键只能包含字母、数字和下划线")
        
        return v.strip()
    
    @field_validator('kl_type')
    @classmethod
    def validate_kl_type(cls, v):
        """验证K线类型"""
        if not v or not v.strip():
            raise ValueError("K线类型不能为空")
        
        # 常见的K线类型
        valid_types = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M']
        if v not in valid_types:
            raise ValueError(f"K线类型必须是以下值之一: {valid_types}")
        
        return v.strip()
    
    @field_validator('time_key')
    @classmethod
    def validate_time_key(cls, v):
        """验证时间键"""
        if not v or not v.strip():
            raise ValueError("时间键不能为空")
        
        return v.strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "ticker_id": self.ticker_id,
            "strategy_key": self.strategy_key,
            "kl_type": self.kl_type,
            "time_key": self.time_key,
            "data": self.data,
            "pos_data": self.pos_data,
            "status": self.status.value,
            "code": self.code,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TickerStrategy":
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
                data["status"] = StrategyStatus(data["status"])
            except ValueError:
                data["status"] = StrategyStatus.ACTIVE
        
        # 处理JSON字段
        for json_field in ["data", "pos_data"]:
            if isinstance(data.get(json_field), str):
                try:
                    import json
                    data[json_field] = json.loads(data[json_field])
                except (json.JSONDecodeError, TypeError):
                    data[json_field] = None
        
        return cls(**data)
    
    def is_active(self) -> bool:
        """检查策略是否处于活跃状态"""
        return self.status == StrategyStatus.ACTIVE
    
    def is_deleted(self) -> bool:
        """检查策略是否已删除"""
        return self.status == StrategyStatus.DELETED
    
    def get_unique_key(self) -> str:
        """获取唯一键（用于去重）"""
        return f"{self.ticker_id}_{self.strategy_key}_{self.kl_type}"
    
    def get_data_count(self) -> int:
        """获取策略数据数量"""
        if not self.data:
            return 0
        
        if isinstance(self.data, list):
            return len(self.data)
        elif isinstance(self.data, dict):
            return len(self.data.keys())
        else:
            return 0
    
    def get_position_count(self) -> int:
        """获取持仓数据数量"""
        if not self.pos_data:
            return 0
        
        if isinstance(self.pos_data, list):
            return len(self.pos_data)
        elif isinstance(self.pos_data, dict):
            return len(self.pos_data.keys())
        else:
            return 0
    
    def get_latest_data(self) -> Optional[Any]:
        """获取最新策略数据"""
        if not self.data:
            return None
        
        if isinstance(self.data, list) and len(self.data) > 0:
            return self.data[-1]
        elif isinstance(self.data, dict):
            # 对于字典类型，返回最后一个键的值
            keys = sorted(self.data.keys())
            if keys:
                return self.data[keys[-1]]
        
        return None
    
    def get_latest_position(self) -> Optional[Any]:
        """获取最新持仓数据"""
        if not self.pos_data:
            return None
        
        if isinstance(self.pos_data, list) and len(self.pos_data) > 0:
            return self.pos_data[-1]
        elif isinstance(self.pos_data, dict):
            # 对于字典类型，返回最后一个键的值
            keys = sorted(self.pos_data.keys())
            if keys:
                return self.pos_data[keys[-1]]
        
        return None
    
    def has_positions(self) -> bool:
        """检查是否有持仓数据"""
        return self.pos_data is not None and len(self.pos_data) > 0
    
    def get_strategy_name(self) -> str:
        """获取策略名称"""
        # 从策略键中提取策略名称
        if '_' in self.strategy_key:
            return self.strategy_key.split('_')[0]
        else:
            return self.strategy_key


class TickerStrategyCreate(BaseModel):
    """创建股票策略的请求模型"""
    ticker_id: int = Field(..., description="股票ID")
    strategy_key: str = Field(..., min_length=1, max_length=100, description="策略键，使用Strategy的getKey值")
    kl_type: str = Field(..., min_length=1, max_length=20, description="K线类型")
    time_key: str = Field(..., min_length=1, max_length=50, description="时间键")
    data: Optional[Union[List[Any], Dict[str, Any]]] = Field(None, description="策略数据")
    pos_data: Optional[Union[List[Any], Dict[str, Any]]] = Field(None, description="持仓数据")
    status: int = Field(StrategyStatus.ACTIVE.value, description="状态")
    code: Optional[str] = Field(None, max_length=50, description="代码")
    version: int = Field(default=1, description="版本号")

    model_config = {"from_attributes": True, "populate_by_name": True}

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """验证状态"""
        try:
            valid_values = [s.value for s in StrategyStatus]
            if v not in valid_values:
                raise ValueError(f"无效的状态: {v}。有效值为: {valid_values}")
            return v
        except Exception as e:
            raise ValueError(f"验证状态失败: {e}")


class TickerStrategyUpdate(BaseModel):
    """更新股票策略的请求模型"""
    time_key: Optional[str] = Field(None, min_length=1, max_length=50, description="时间键")
    data: Optional[Union[List[Any], Dict[str, Any]]] = Field(None, description="策略数据")
    pos_data: Optional[Union[List[Any], Dict[str, Any]]] = Field(None, description="持仓数据")
    status: Optional[int] = Field(None, description="状态")
    code: Optional[str] = Field(None, max_length=50, description="代码")
    version: Optional[int] = Field(None, description="版本号")


class TickerStrategyDTO(BaseModel):
    """股票策略响应模型"""
    id: int = Field(..., description="策略ID")
    ticker_id: int = Field(..., description="股票ID")
    strategy_key: str = Field(..., description="策略键，使用Strategy的getKey值")
    kl_type: str = Field(..., description="K线类型")
    time_key: str = Field(..., description="时间键")
    data: Optional[Union[List[Any], Dict[str, Any]]] = Field(None, description="策略数据")
    pos_data: Optional[Union[List[Any], Dict[str, Any]]] = Field(None, description="持仓数据")
    status: StrategyStatus = Field(..., description="状态")
    code: Optional[str] = Field(None, description="代码")
    version: int = Field(..., description="版本号")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # Pydantic v2 配置
    model_config = {"from_attributes": True, "populate_by_name": True}

    @classmethod
    def from_entity(cls, strategy: TickerStrategy) -> "TickerStrategyDTO":
        """从实体对象创建响应模型"""
        return cls(
            id=strategy.id,
            ticker_id=strategy.ticker_id,
            strategy_key=strategy.strategy_key,
            kl_type=strategy.kl_type,
            time_key=strategy.time_key,
            data=strategy.data,
            pos_data=strategy.pos_data,
            status=strategy.status,
            code=strategy.code,
            version=strategy.version,
            created_at=strategy.created_at,
            updated_at=strategy.updated_at
        ) 