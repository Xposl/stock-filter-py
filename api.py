from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from core.Handler import DataSourceHelper
import datetime

app = FastAPI(title="InvestNote API")
dataSource = DataSourceHelper()

class TickerRequest(BaseModel):
    market: str  # 'hk', 'zh', 'us'
    code: str
    is_real_time: Optional[bool] = False
    days: Optional[int] = 250

@app.get("/")
async def root():
    return {"message": "InvestNote API Service"}

@app.post("/update/ticker-list")
async def update_ticker_list():
    try:
        dataSource.updateTickerList()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analysis/ticker")
async def analysis_ticker(request: TickerRequest):
    try:
        code = format_ticker_code(request.market, request.code)
        if code is None:
            raise HTTPException(status_code=400, detail="Invalid market or code")
            
        dataSource.updateTickerByCode(code, request.is_real_time)
        if request.is_real_time:
            result = dataSource.analysisTickerOnTime(code, request.days)
        else:
            result = dataSource.analysisTicker(code, request.days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update/recommend")
async def update_recommend():
    try:
        dataSource.updateRecommendTickers()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update/project/{project_id}")
async def update_project(project_id: int, start_key: Optional[str] = None):
    try:
        tickers = dataSource.getProjectTickers(project_id, start_key)
        dataSource.updateTickers(tickers)
        return {"status": "success", "tickers": tickers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def format_ticker_code(market: str, code: str) -> Optional[str]:
    if market == 'hk':
        return f'HK.{code.zfill(5)}'
    elif market == 'zh':
        code = code.zfill(6)
        if code.startswith(('0', '3')):
            return f'SZ.{code}'
        elif code.startswith(('6', '7', '9')):
            return f'SH.{code}'
    elif market == 'us':
        return f'US.{code}'
    return None
