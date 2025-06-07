#!/usr/bin/env python3

from datetime import datetime, time
from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class MarketBase(BaseModel):
    """Market基础模型，包含共有字段"""

    code: str = Field(..., description="市场代码", min_length=1, max_length=10)
    name: str = Field(..., description="市场名称")
    region: str = Field(..., description="地区")
    currency: str = Field(default="USD", description="货币代码")
    timezone: str = Field(..., description="时区，如 Asia/Shanghai")
    open_time: time = Field(..., description="开盘时间")
    close_time: time = Field(..., description="收盘时间")
    trading_days: str = Field(default="Mon,Tue,Wed,Thu,Fri", description="交易日，逗号分隔")
    status: int = Field(default=1, description="状态：1=活跃，0=停用")

    model_config = ConfigDict(from_attributes=True)


class MarketCreate(MarketBase):
    """用于创建Market的模型"""

    pass


class MarketUpdate(BaseModel):
    """用于更新Market的模型，所有字段都是可选的"""

    code: Optional[str] = Field(default=None, description="市场代码")
    name: Optional[str] = Field(default=None, description="市场名称")
    region: Optional[str] = Field(default=None, description="地区")
    currency: Optional[str] = Field(default=None, description="货币代码")
    timezone: Optional[str] = Field(default=None, description="时区")
    open_time: Optional[time] = Field(default=None, description="开盘时间")
    close_time: Optional[time] = Field(default=None, description="收盘时间")
    trading_days: Optional[str] = Field(default=None, description="交易日")
    status: Optional[int] = Field(default=None, description="状态")

    model_config = ConfigDict(from_attributes=True)


class Market(MarketBase):
    """完整的Market模型，包含ID"""

    id: int = Field(..., description="ID")
    created_at: Optional[datetime] = Field(
        default_factory=datetime.now, description="创建时间"
    )
    updated_at: Optional[datetime] = Field(
        default_factory=datetime.now, description="更新时间"
    )

    model_config = ConfigDict(from_attributes=True)

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

    def get_trading_days_list(self) -> list[str]:
        """
        获取交易日列表

        Returns:
            交易日列表，如 ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
        """
        return [day.strip() for day in self.trading_days.split(",") if day.strip()]


# 用于序列化和反序列化的辅助函数
def market_to_dict(market: Union[Market, MarketCreate, MarketUpdate]) -> dict:
    """
    将Market模型转换为字典，用于数据库操作

    Args:
        market: Market、MarketCreate或MarketUpdate模型

    Returns:
        字典表示
    """
    if isinstance(market, (MarketCreate, MarketUpdate)):
        result = market.model_dump(exclude_unset=True, exclude_none=True)
    else:
        result = market.model_dump(exclude_none=True)

    # 处理时间字段转换为字符串
    if "open_time" in result and result["open_time"] is not None:
        if isinstance(result["open_time"], time):
            result["open_time"] = result["open_time"].strftime("%H:%M:%S")

    if "close_time" in result and result["close_time"] is not None:
        if isinstance(result["close_time"], time):
            result["close_time"] = result["close_time"].strftime("%H:%M:%S")

    return result


def dict_to_market(data: dict) -> Market:
    """
    将字典转换为Market模型，处理各种数据类型转换和默认值

    Args:
        data: 来自数据库的字典数据

    Returns:
        Market模型实例
    """
    # 创建数据的副本，避免修改原始数据
    processed_data = data.copy()

    # 处理状态字段
    processed_data["status"] = int(processed_data.get("status", 1) or 1)

    # 处理时间字段（将字符串转换为time对象）
    for time_field in ["open_time", "close_time"]:
        if time_field in processed_data:
            time_value = processed_data[time_field]

            # 如果是None或空字符串，设为None
            if time_value is None or (
                isinstance(time_value, str) and not time_value.strip()
            ):
                processed_data[time_field] = None
                continue

            # 如果已经是time对象，保持不变
            if isinstance(time_value, time):
                continue

            # 尝试将字符串转换为time
            if isinstance(time_value, str):
                try:
                    # 尝试HH:MM:SS格式
                    processed_data[time_field] = datetime.strptime(
                        time_value, "%H:%M:%S"
                    ).time()
                except ValueError:
                    try:
                        # 尝试HH:MM格式
                        processed_data[time_field] = datetime.strptime(
                            time_value, "%H:%M"
                        ).time()
                    except ValueError:
                        processed_data[time_field] = None

    # 处理日期字段
    for date_field in ["created_at", "updated_at"]:
        if date_field in processed_data:
            date_value = processed_data[date_field]
            if isinstance(date_value, str) and date_value:
                try:
                    processed_data[date_field] = datetime.fromisoformat(
                        date_value.replace("Z", "+00:00")
                    )
                except (ValueError, AttributeError):
                    try:
                        processed_data[date_field] = datetime.strptime(
                            date_value, "%Y-%m-%d %H:%M:%S"
                        )
                    except (ValueError, AttributeError):
                        processed_data[date_field] = None

    try:
        # 创建Market模型实例
        return Market(**processed_data)
    except Exception as e:
        print(f"无法创建Market模型: {e}")
        print(f"数据: {processed_data}")

        # 返回带有最小必要字段的Market（用于错误恢复）
        return Market(
            id=processed_data.get("id", 0),
            code=processed_data.get("code", "unknown"),
            name=processed_data.get("name", "Unknown Market"),
            region=processed_data.get("region", "Unknown"),
            timezone=processed_data.get("timezone", "UTC"),
            open_time=time(9, 30),  # 默认09:30
            close_time=time(16, 0),  # 默认16:00
            status=1,
        )
