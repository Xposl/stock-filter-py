from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from core.handler.data_source_helper import DataSourceHelper
import datetime

app = FastAPI(title="InvestNote API")
dataSource = DataSourceHelper()

class TickerRequest(BaseModel):
    market: str  # 'hk', 'zh', 'us'
    code: str
    is_real_time: Optional[bool] = False
    days: Optional[int] = 250

class TickerQuery(BaseModel):
    market: str  # 'hk', 'zh', 'us'
    code: str
    days: Optional[int] = 250

@app.get("/")
async def root():
    return {"message": "InvestNote API Service"}



@app.post("/update/project/{project_id}")
async def update_project(project_id: int, start_key: Optional[str] = None):
    try:
        tickers = dataSource.getProjectTickers(project_id, start_key)
        dataSource.updateTickers(tickers)
        return {"status": "success", "tickers": tickers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))