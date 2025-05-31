# InvestNote-py 样式指南

## 代码风格规范

### Python代码风格

#### 基础规范
- **遵循PEP 8**: 严格按照Python官方代码风格指南
- **行长度**: 最大88字符（Black格式化器默认）
- **缩进**: 使用4个空格，不使用制表符
- **编码**: 统一使用UTF-8编码

#### 命名约定
```python
# 变量和函数名：snake_case
user_id = 123
def get_stock_data():
    pass

# 类名：PascalCase
class StockAnalyzer:
    pass

# 常量：UPPER_SNAKE_CASE
MAX_RETRY_COUNT = 3
API_BASE_URL = "https://api.example.com"

# 私有成员：下划线前缀
class DataProcessor:
    def __init__(self):
        self._private_data = None
        self.__very_private = None
```

#### 导入规范
```python
# 标准库导入
import os
import sys
from datetime import datetime, timedelta

# 第三方库导入
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException

# 本地应用导入
from core.models import Stock
from core.services import DataService
```

### FastAPI特定规范

#### 路由定义
```python
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

router = APIRouter(prefix="/api/v1/stocks", tags=["stocks"])

@router.get("/{stock_id}", response_model=StockResponse)
async def get_stock(
    stock_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> StockResponse:
    """
    获取股票详细信息
    
    - **stock_id**: 股票ID
    - **返回**: 股票详细信息
    """
    if stock := await stock_service.get_by_id(db, stock_id):
        return stock
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Stock not found"
    )
```

#### Pydantic模型规范
```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class MarketEnum(str, Enum):
    US = "us"
    HK = "hk"
    CN = "cn"

class StockBase(BaseModel):
    """股票基础模型"""
    symbol: str = Field(..., description="股票代码", example="AAPL")
    name: str = Field(..., description="股票名称", example="Apple Inc.")
    market: MarketEnum = Field(..., description="市场")
    
    @validator('symbol')
    def symbol_must_be_uppercase(cls, v):
        return v.upper()

class StockCreate(StockBase):
    """创建股票模型"""
    pass

class StockResponse(StockBase):
    """股票响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
```

#### 依赖注入规范
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

security = HTTPBearer()

async def get_db() -> AsyncSession:
    """获取数据库会话"""
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_current_user(
    token: str = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前用户"""
    try:
        payload = decode_token(token.credentials)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return await user_service.get_by_id(db, user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
```

### 数据库模型规范

#### SQLAlchemy模型
```python
from sqlalchemy import Column, Integer, String, DateTime, Float, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from core.enums import MarketEnum

Base = declarative_base()

class Stock(Base):
    """股票数据模型"""
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    market = Column(SQLEnum(MarketEnum), nullable=False)
    
    # 时间戳
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    def __repr__(self):
        return f"<Stock(symbol='{self.symbol}', name='{self.name}')>"
```

### 异常处理规范

#### 自定义异常
```python
class InvestNoteException(Exception):
    """投资笔记系统基础异常"""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(self.message)

class DataSourceException(InvestNoteException):
    """数据源异常"""
    pass

class ValidationException(InvestNoteException):
    """验证异常"""
    pass
```

#### 异常处理器
```python
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger(__name__)

@app.exception_handler(InvestNoteException)
async def investnote_exception_handler(
    request: Request, 
    exc: InvestNoteException
):
    logger.error(f"InvestNote异常: {exc.message}")
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "message": exc.message,
                "code": exc.code,
                "type": exc.__class__.__name__
            }
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "message": "Validation error",
                "details": exc.errors()
            }
        }
    )
```

### 日志规范

#### 日志配置
```python
import logging
from datetime import datetime

# 日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 配置根日志器
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/app_{datetime.now().strftime('%Y%m%d')}.log")
    ]
)

# 模块日志器
logger = logging.getLogger(__name__)
```

#### 日志使用规范
```python
import logging

logger = logging.getLogger(__name__)

async def process_stock_data(symbol: str):
    logger.info(f"开始处理股票数据: {symbol}")
    
    try:
        # 业务逻辑
        data = await fetch_stock_data(symbol)
        logger.debug(f"获取到数据条数: {len(data)}")
        
        result = await analyze_data(data)
        logger.info(f"股票 {symbol} 处理完成")
        
        return result
        
    except DataSourceException as e:
        logger.error(f"数据源错误 {symbol}: {e.message}")
        raise
        
    except Exception as e:
        logger.exception(f"处理股票数据时发生未知错误 {symbol}")
        raise
```

### 测试规范

#### 测试文件组织
```
tests/
├── unit/                   # 单元测试
│   ├── test_models.py
│   ├── test_services.py
│   └── test_utils.py
├── integration/            # 集成测试
│   ├── test_api.py
│   └── test_database.py
├── conftest.py            # pytest配置
└── __init__.py
```

#### 测试代码规范
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from core.models import Stock
from core.schemas import StockCreate

client = TestClient(app)

class TestStockAPI:
    """股票API测试类"""
    
    @pytest.mark.asyncio
    async def test_create_stock_success(self, db_session: AsyncSession):
        """测试成功创建股票"""
        # Arrange
        stock_data = {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "market": "us"
        }
        
        # Act
        response = client.post("/api/v1/stocks/", json=stock_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["name"] == "Apple Inc."
    
    def test_get_stock_not_found(self):
        """测试获取不存在的股票"""
        response = client.get("/api/v1/stocks/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
```

### 文档规范

#### Docstring格式
```python
def calculate_moving_average(prices: List[float], period: int) -> List[float]:
    """
    计算移动平均线
    
    Args:
        prices: 价格列表
        period: 周期数
        
    Returns:
        移动平均值列表
        
    Raises:
        ValueError: 当period大于prices长度时
        
    Example:
        >>> prices = [1.0, 2.0, 3.0, 4.0, 5.0]
        >>> calculate_moving_average(prices, 3)
        [2.0, 3.0, 4.0]
    """
    if period > len(prices):
        raise ValueError("Period cannot be greater than prices length")
    
    # 实现代码...
```

#### API文档规范
```python
@router.post(
    "/stocks/",
    response_model=StockResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建股票",
    description="创建新的股票记录",
    response_description="创建成功的股票信息",
    tags=["stocks"]
)
async def create_stock(
    stock: StockCreate,
    db: AsyncSession = Depends(get_db)
) -> StockResponse:
    """
    创建新股票记录
    
    - **symbol**: 股票代码（必需）
    - **name**: 股票名称（必需）
    - **market**: 所属市场（必需）
    """
    return await stock_service.create(db, stock)
```

### 配置管理规范

#### 环境配置
```python
from pydantic import BaseSettings, Field
from typing import Optional

class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    app_name: str = "InvestNote API"
    debug: bool = False
    version: str = "1.0.0"
    
    # 数据库配置
    database_url: str = Field(..., env="DATABASE_URL")
    
    # 认证配置
    secret_key: str = Field(..., env="SECRET_KEY")
    access_token_expire_minutes: int = 30
    
    # 外部服务配置
    auth_service_host: str = Field(default="localhost", env="AUTH_SERVICE_HOST")
    auth_service_port: int = Field(default=50051, env="AUTH_SERVICE_PORT")
    
    # 数据源配置
    akshare_enabled: bool = Field(default=True, env="AKSHARE_ENABLED")
    futu_enabled: bool = Field(default=True, env="FUTU_ENABLED")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# 全局配置实例
settings = Settings()
```

这些样式规范确保了代码的一致性、可读性和可维护性，为项目的长期发展奠定了良好的基础。 