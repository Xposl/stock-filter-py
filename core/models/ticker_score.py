#!/usr/bin/env python3

from datetime import datetime
from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class TickerScoreBase(BaseModel):
    """评分基础模型，包含共有字段"""

    ticker_id: int = Field(..., description="股票ID")
    time_key: str = Field(..., description="时间键")
    ma_buy: float = Field(default=0.0, description="MA买入信号强度")
    ma_sell: float = Field(default=0.0, description="MA卖出信号强度")
    ma_score: float = Field(default=0.0, description="MA分数")
    in_buy: float = Field(default=0.0, description="指标买入信号强度")
    in_sell: float = Field(default=0.0, description="指标卖出信号强度")
    in_score: float = Field(default=0.0, description="指标分数")
    strategy_buy: int = Field(default=0, description="策略买入信号数")
    strategy_sell: int = Field(default=0, description="策略卖出信号数")
    strategy_score: float = Field(default=0.0, description="策略分数")
    score: float = Field(default=0.0, description="综合分数")
    history: Optional[Union[list[Any], dict[str, Any]]] = Field(
        default=None, description="历史数据"
    )

    model_config = ConfigDict(from_attributes=True)


class TickerScoreCreate(TickerScoreBase):
    """用于创建评分的模型"""

    pass


class TickerScoreUpdate(BaseModel):
    """用于更新评分的模型，所有字段都是可选的"""

    time_key: Optional[str] = Field(default=None, description="时间键")
    ma_buy: Optional[float] = Field(default=None, description="MA买入信号数")
    ma_sell: Optional[float] = Field(default=None, description="MA卖出信号数")
    ma_score: Optional[float] = Field(default=None, description="MA分数")
    in_buy: Optional[float] = Field(default=None, description="指标买入信号数")
    in_sell: Optional[float] = Field(default=None, description="指标卖出信号数")
    in_score: Optional[float] = Field(default=None, description="指标分数")
    strategy_buy: Optional[float] = Field(default=None, description="策略买入信号数")
    strategy_sell: Optional[float] = Field(default=None, description="策略卖出信号数")
    strategy_score: Optional[float] = Field(default=None, description="策略分数")
    score: Optional[float] = Field(default=None, description="综合分数")
    history: Optional[Union[list[Any], dict[str, Any]]] = Field(
        default=None, description="历史数据"
    )
    model_config = ConfigDict(from_attributes=True)


class TickerScore(TickerScoreBase):
    """完整的评分模型，包含ID"""

    id: int = Field(..., description="ID")
    status: Optional[int] = Field(default=1, description="状态")
    create_time: Optional[datetime] = Field(
        default_factory=datetime.now, description="创建时间"
    )

    model_config = ConfigDict(from_attributes=True)


# 用于序列化和反序列化的辅助函数
def ticker_score_to_dict(score: Any) -> dict:
    """
    将TickerScore模型转换为字典，用于数据库操作

    Args:
        score: TickerScore、TickerScoreCreate或TickerScoreUpdate模型

    Returns:
        字典表示
    """
    result = {}

    if isinstance(score, (TickerScoreCreate, TickerScoreUpdate)):
        result = score.model_dump(exclude_unset=True, exclude_none=True)
    else:
        result = score.model_dump(exclude_none=True)

    # 处理JSON字段
    if "history" in result and result["history"] is not None:
        import json

        result["history"] = json.dumps(result["history"])

    return result


def dict_to_ticker_score(data: dict) -> TickerScore:
    """
    将字典转换为TickerScore模型，处理各种数据类型转换和默认值

    Args:
        data: 来自数据库的字典数据

    Returns:
        TickerScore模型实例
    """
    # 创建数据的副本，避免修改原始数据
    processed_data = data.copy()

    # 处理JSON字段
    if "history" in processed_data:
        json_value = processed_data["history"]

        # 如果是None或空字符串，设为None
        if json_value is None or (
            isinstance(json_value, str) and not json_value.strip()
        ):
            processed_data["history"] = None
        # 如果已经是字典或列表对象，保持不变
        elif isinstance(json_value, (dict, list)):
            pass
        # 尝试解析JSON字符串
        elif isinstance(json_value, str):
            try:
                import json

                processed_data["history"] = json.loads(json_value)
            except (ValueError, json.JSONDecodeError):
                processed_data["history"] = None

    # 确保必要字段存在并有默认值
    processed_data["status"] = int(processed_data.get("status", 1) or 1)

    # 确保数值字段是正确的类型
    for float_field in [
        "ma_buy",
        "ma_sell",
        "in_buy",
        "in_sell",
        "ma_score",
        "in_score",
        "strategy_score",
        "score",
    ]:
        if float_field in processed_data and processed_data[float_field] is not None:
            processed_data[float_field] = float(processed_data[float_field])

    for int_field in ["strategy_buy", "strategy_sell"]:
        if int_field in processed_data and processed_data[int_field] is not None:
            processed_data[int_field] = int(processed_data[int_field])

    # 处理日期字段(如果是字符串格式)
    if "create_time" in processed_data:
        date_value = processed_data["create_time"]

        # 如果是None或空字符串，设为当前时间
        if date_value is None or (
            isinstance(date_value, str) and not date_value.strip()
        ):
            processed_data["create_time"] = datetime.now()
        elif isinstance(date_value, str):
            try:
                # 尝试ISO格式
                processed_data["create_time"] = datetime.fromisoformat(
                    date_value.replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                try:
                    # 尝试标准MySQL格式
                    processed_data["create_time"] = datetime.strptime(
                        date_value, "%Y-%m-%d %H:%M:%S"
                    )
                except (ValueError, AttributeError):
                    processed_data["create_time"] = datetime.now()

    try:
        # 创建TickerScore模型实例
        return TickerScore(**processed_data)
    except Exception as e:
        print(f"无法创建TickerScore模型: {e}")
        print(f"数据: {processed_data}")

        # 返回带有最小必要字段的TickerScore（用于错误恢复）
        return TickerScore(
            id=processed_data.get("id", 0),
            ticker_id=processed_data.get("ticker_id", 0),
            time_key=processed_data.get("time_key", ""),
            ma_buy=0,
            ma_sell=0,
            ma_score=0.0,
            in_buy=0,
            in_sell=0,
            in_score=0.0,
            strategy_buy=0,
            strategy_sell=0,
            strategy_score=0.0,
            score=0.0,
            status=1,
        )
