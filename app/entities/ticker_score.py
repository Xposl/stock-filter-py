"""
股票评分实体类
定义股票评分的数据结构和业务逻辑
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, ClassVar, List

from pydantic import BaseModel, Field, field_validator


class ScoreStatus(int, Enum):
    """评分状态枚举"""
    ACTIVE = 1      # 活跃
    INACTIVE = 0    # 非活跃
    DELETED = -1    # 已删除


class TickerScore(BaseModel):
    """
    股票评分实体类: 定义股票评分的基本信息和元数据
    """
    
    # 数据库表定义
    TABLE_NAME: ClassVar[str] = "ticker_scores"
    TABLE_SCHEMA: ClassVar[str] = """
    CREATE TABLE IF NOT EXISTS ticker_scores (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        ticker_id INT NOT NULL COMMENT '股票ID',
        time_key VARCHAR(50) NOT NULL COMMENT '时间键',
        ma_buy DECIMAL(10,4) DEFAULT 0.0 COMMENT 'MA买入信号强度',
        ma_sell DECIMAL(10,4) DEFAULT 0.0 COMMENT 'MA卖出信号强度',
        ma_score DECIMAL(10,4) DEFAULT 0.0 COMMENT 'MA分数',
        in_buy DECIMAL(10,4) DEFAULT 0.0 COMMENT '指标买入信号强度',
        in_sell DECIMAL(10,4) DEFAULT 0.0 COMMENT '指标卖出信号强度',
        in_score DECIMAL(10,4) DEFAULT 0.0 COMMENT '指标分数',
        strategy_buy INT DEFAULT 0 COMMENT '策略买入信号数',
        strategy_sell INT DEFAULT 0 COMMENT '策略卖出信号数',
        strategy_score DECIMAL(10,4) DEFAULT 0.0 COMMENT '策略分数',
        score DECIMAL(10,4) DEFAULT 0.0 COMMENT '综合分数',
        history JSON COMMENT '历史评分数组，存储每日评分记录',
        analysis_data JSON COMMENT '分析数据（如raw_score, z_score, trend_strength等）',
        status INT DEFAULT 1 COMMENT '状态：1-活跃，0-非活跃，-1-已删除',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        
        INDEX idx_ticker_id (ticker_id),
        INDEX idx_time_key (time_key),
        INDEX idx_score (score),
        INDEX idx_status (status),
        INDEX idx_created_at (created_at),
        UNIQUE KEY uk_ticker_time (ticker_id, time_key)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票评分表'
    """
    
    id: Optional[int] = Field(None, description="评分ID")
    ticker_id: int = Field(..., description="股票ID")
    time_key: str = Field(..., min_length=1, max_length=50, description="时间键")
    ma_buy: float = Field(default=0.0, ge=0.0, description="MA买入信号强度")
    ma_sell: float = Field(default=0.0, ge=0.0, description="MA卖出信号强度")
    ma_score: float = Field(default=0.0, description="MA分数")
    in_buy: float = Field(default=0.0, ge=0.0, description="指标买入信号强度")
    in_sell: float = Field(default=0.0, ge=0.0, description="指标卖出信号强度")
    in_score: float = Field(default=0.0, description="指标分数")
    strategy_buy: int = Field(default=0, ge=0, description="策略买入信号数")
    strategy_sell: int = Field(default=0, ge=0, description="策略卖出信号数")
    strategy_score: float = Field(default=0.0, description="策略分数")
    score: float = Field(default=0.0, description="综合分数")
    history: Optional[List[Dict[str, Any]]] = Field(None, description="历史评分数组，存储每日评分记录")
    analysis_data: Optional[Dict[str, Any]] = Field(None, description="分析数据（如raw_score, z_score, trend_strength等）")
    status: ScoreStatus = Field(ScoreStatus.ACTIVE, description="状态")
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
    
    @field_validator('time_key')
    @classmethod
    def validate_time_key(cls, v):
        """验证时间键"""
        if not v or not v.strip():
            raise ValueError("时间键不能为空")
        
        return v.strip()
    
    @field_validator('score')
    @classmethod
    def validate_score(cls, v):
        """验证综合分数"""
        if v < -100.0 or v > 100.0:
            raise ValueError("综合分数必须在-100到100之间")
        return v
    
    @field_validator('ma_score', 'in_score', 'strategy_score')
    @classmethod
    def validate_component_scores(cls, v):
        """验证各组件分数"""
        if v < -100.0 or v > 100.0:
            raise ValueError("组件分数必须在-100到100之间")
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "ticker_id": self.ticker_id,
            "time_key": self.time_key,
            "ma_buy": self.ma_buy,
            "ma_sell": self.ma_sell,
            "ma_score": self.ma_score,
            "in_buy": self.in_buy,
            "in_sell": self.in_sell,
            "in_score": self.in_score,
            "strategy_buy": self.strategy_buy,
            "strategy_sell": self.strategy_sell,
            "strategy_score": self.strategy_score,
            "score": self.score,
            "history": self.history,
            "analysis_data": self.analysis_data,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TickerScore":
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
                data["status"] = ScoreStatus(data["status"])
            except ValueError:
                data["status"] = ScoreStatus.ACTIVE
        
        # 处理JSON字段
        for json_field in ["history", "analysis_data"]:
            if isinstance(data.get(json_field), str):
                try:
                    import json
                    data[json_field] = json.loads(data[json_field])
                except (json.JSONDecodeError, TypeError):
                    data[json_field] = None
        
        return cls(**data)
    
    def is_active(self) -> bool:
        """检查评分是否处于活跃状态"""
        return self.status == ScoreStatus.ACTIVE
    
    def is_deleted(self) -> bool:
        """检查评分是否已删除"""
        return self.status == ScoreStatus.DELETED
    
    def get_buy_signal_strength(self) -> float:
        """获取买入信号强度"""
        return self.ma_buy + self.in_buy
    
    def get_sell_signal_strength(self) -> float:
        """获取卖出信号强度"""
        return self.ma_sell + self.in_sell
    
    def get_signal_balance(self) -> float:
        """获取信号平衡度（正值表示买入信号强，负值表示卖出信号强）"""
        return self.get_buy_signal_strength() - self.get_sell_signal_strength()
    
    def get_score_level(self) -> str:
        """获取评分等级"""
        if self.score >= 80:
            return "优秀"
        elif self.score >= 60:
            return "良好"
        elif self.score >= 40:
            return "一般"
        elif self.score >= 20:
            return "较差"
        else:
            return "很差"
    
    def get_trend_direction(self) -> str:
        """获取趋势方向"""
        if self.score > 0:
            return "上涨"
        elif self.score < 0:
            return "下跌"
        else:
            return "横盘"
    
    def calculate_composite_score(self) -> float:
        """计算综合分数（加权平均）"""
        # 权重配置
        ma_weight = 0.3
        indicator_weight = 0.4
        strategy_weight = 0.3
        
        composite_score = (
            self.ma_score * ma_weight +
            self.in_score * indicator_weight +
            self.strategy_score * strategy_weight
        )
        
        return round(composite_score, 4)
    
    def add_history_record(self, record: Dict[str, Any]) -> None:
        """添加历史记录"""
        if self.history is None:
            self.history = []
        
        # 添加时间戳
        record["timestamp"] = datetime.now().isoformat()
        self.history.append(record)
        
        # 限制历史记录数量（保留最近100条）
        if len(self.history) > 100:
            self.history = self.history[-100:]


class TickerScoreCreate(BaseModel):
    """创建股票评分的请求模型"""
    ticker_id: int = Field(..., description="股票ID")
    time_key: str = Field(..., min_length=1, max_length=50, description="时间键")
    ma_buy: float = Field(default=0.0, ge=0.0, description="MA买入信号强度")
    ma_sell: float = Field(default=0.0, ge=0.0, description="MA卖出信号强度")
    ma_score: float = Field(default=0.0, description="MA分数")
    in_buy: float = Field(default=0.0, ge=0.0, description="指标买入信号强度")
    in_sell: float = Field(default=0.0, ge=0.0, description="指标卖出信号强度")
    in_score: float = Field(default=0.0, description="指标分数")
    strategy_buy: int = Field(default=0, ge=0, description="策略买入信号数")
    strategy_sell: int = Field(default=0, ge=0, description="策略卖出信号数")
    strategy_score: float = Field(default=0.0, description="策略分数")
    score: float = Field(default=0.0, description="综合分数")
    history: Optional[List[Dict[str, Any]]] = Field(None, description="历史评分数组，存储每日评分记录")
    analysis_data: Optional[Dict[str, Any]] = Field(None, description="分析数据（如raw_score, z_score, trend_strength等）")
    status: int = Field(ScoreStatus.ACTIVE.value, description="状态")

    model_config = {"from_attributes": True, "populate_by_name": True}

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """验证状态"""
        try:
            valid_values = [s.value for s in ScoreStatus]
            if v not in valid_values:
                raise ValueError(f"无效的状态: {v}。有效值为: {valid_values}")
            return v
        except Exception as e:
            raise ValueError(f"验证状态失败: {e}")


class TickerScoreUpdate(BaseModel):
    """更新股票评分的请求模型"""
    time_key: Optional[str] = Field(None, min_length=1, max_length=50, description="时间键")
    ma_buy: Optional[float] = Field(None, ge=0.0, description="MA买入信号强度")
    ma_sell: Optional[float] = Field(None, ge=0.0, description="MA卖出信号强度")
    ma_score: Optional[float] = Field(None, description="MA分数")
    in_buy: Optional[float] = Field(None, ge=0.0, description="指标买入信号强度")
    in_sell: Optional[float] = Field(None, ge=0.0, description="指标卖出信号强度")
    in_score: Optional[float] = Field(None, description="指标分数")
    strategy_buy: Optional[int] = Field(None, ge=0, description="策略买入信号数")
    strategy_sell: Optional[int] = Field(None, ge=0, description="策略卖出信号数")
    strategy_score: Optional[float] = Field(None, description="策略分数")
    score: Optional[float] = Field(None, description="综合分数")
    history: Optional[List[Dict[str, Any]]] = Field(None, description="历史评分数组，存储每日评分记录")
    analysis_data: Optional[Dict[str, Any]] = Field(None, description="分析数据（如raw_score, z_score, trend_strength等）")
    status: Optional[int] = Field(None, description="状态")


class TickerScoreDTO(BaseModel):
    """股票评分响应模型"""
    id: int = Field(..., description="评分ID")
    ticker_id: int = Field(..., description="股票ID")
    time_key: str = Field(..., description="时间键")
    ma_buy: float = Field(..., description="MA买入信号强度")
    ma_sell: float = Field(..., description="MA卖出信号强度")
    ma_score: float = Field(..., description="MA分数")
    in_buy: float = Field(..., description="指标买入信号强度")
    in_sell: float = Field(..., description="指标卖出信号强度")
    in_score: float = Field(..., description="指标分数")
    strategy_buy: int = Field(..., description="策略买入信号数")
    strategy_sell: int = Field(..., description="策略卖出信号数")
    strategy_score: float = Field(..., description="策略分数")
    score: float = Field(..., description="综合分数")
    history: Optional[List[Dict[str, Any]]] = Field(None, description="历史评分数组，存储每日评分记录")
    analysis_data: Optional[Dict[str, Any]] = Field(None, description="分析数据（如raw_score, z_score, trend_strength等）")
    status: ScoreStatus = Field(..., description="状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    # Pydantic v2 配置
    model_config = {"from_attributes": True, "populate_by_name": True}

    @classmethod
    def from_entity(cls, score: TickerScore) -> "TickerScoreDTO":
        """从实体对象创建响应模型"""
        return cls(
            id=score.id,
            ticker_id=score.ticker_id,
            time_key=score.time_key,
            ma_buy=score.ma_buy,
            ma_sell=score.ma_sell,
            ma_score=score.ma_score,
            in_buy=score.in_buy,
            in_sell=score.in_sell,
            in_score=score.in_score,
            strategy_buy=score.strategy_buy,
            strategy_sell=score.strategy_sell,
            strategy_score=score.strategy_score,
            score=score.score,
            history=score.history,
            analysis_data=score.analysis_data,
            status=score.status,
            created_at=score.created_at,
            updated_at=score.updated_at
        ) 