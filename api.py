from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from core.handler.data_source_helper import DataSourceHelper

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



@app.get("/ticker/{market}/{ticker_code}")
async def get_ticker_data(market: str, ticker_code: str, days: Optional[int] = 600):
    try:
        code = dataSource.get_ticker_code(market,ticker_code)
        ticker,kLineData,scoreData = dataSource.get_ticker_data(market,code,days)
        return {
            "status": "success", 
            "ticker": ticker,
            "kLineData": kLineData,
            "scoreData": scoreData
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))