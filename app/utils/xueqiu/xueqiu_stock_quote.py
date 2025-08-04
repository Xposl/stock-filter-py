from dataclasses import dataclass
from typing import Optional


@dataclass
class XueqiuStockQuoteMarket:
    status_id: Optional[int] = None
    region: Optional[str] = None
    status: Optional[str] = None
    time_zone: Optional[str] = None
    time_zone_desc: Optional[str] = None
    delay_tag: Optional[int] = None


@dataclass
class XueqiuStockQuoteQuote:
    current_ext: Optional[float] = None
    symbol: Optional[str] = None
    high52w: Optional[float] = None
    percent_ext: Optional[float] = None
    delayed: Optional[int] = None
    type: Optional[int] = None
    tick_size: Optional[float] = None
    float_shares: Optional[float] = None
    high: Optional[float] = None
    float_market_capital: Optional[float] = None
    timestamp_ext: Optional[int] = None
    lot_size: Optional[int] = None
    lock_set: Optional[int] = None
    chg: Optional[float] = None
    eps: Optional[float] = None
    last_close: Optional[float] = None
    profit_four: Optional[float] = None
    volume: Optional[float] = None
    volume_ratio: Optional[float] = None
    profit_forecast: Optional[float] = None
    turnover_rate: Optional[float] = None
    low52w: Optional[float] = None
    name: Optional[str] = None
    exchange: Optional[str] = None
    pe_forecast: Optional[float] = None
    total_shares: Optional[float] = None
    status: Optional[int] = None
    code: Optional[str] = None
    goodwill_in_net_assets: Optional[float] = None
    avg_price: Optional[float] = None
    percent: Optional[float] = None
    psr: Optional[float] = None
    amplitude: Optional[float] = None
    current: Optional[float] = None
    current_year_percent: Optional[float] = None
    issue_date: Optional[int] = None
    sub_type: Optional[str] = None
    low: Optional[float] = None
    market_capital: Optional[float] = None
    shareholder_funds: Optional[float] = None
    dividend: Optional[float] = None
    dividend_yield: Optional[float] = None
    currency: Optional[str] = None
    chg_ext: Optional[float] = None
    navps: Optional[float] = None
    profit: Optional[float] = None
    beta: Optional[float] = None
    timestamp: Optional[int] = None
    pe_lyr: Optional[float] = None
    amount: Optional[float] = None
    pledge_ratio: Optional[float] = None
    short_ratio: Optional[float] = None
    inst_hld: Optional[float] = None
    pb: Optional[float] = None
    pe_ttm: Optional[float] = None
    contract_size: Optional[float] = None
    variable_tick_size: Optional[str] = None
    time: Optional[int] = None
    open: Optional[float] = None


@dataclass
class XueqiuStockQuoteOthers:
    pankou_ratio: Optional[float] = None
    cyb_switch: Optional[bool] = None


@dataclass
class XueqiuStockQuoteTags:
    description: Optional[str] = None
    value: Optional[int] = None


@dataclass
class XueqiuStockQuote:
    market: Optional[XueqiuStockQuoteMarket] = None
    quote: Optional[XueqiuStockQuoteQuote] = None
    others: Optional[XueqiuStockQuoteOthers] = None
    tags: Optional[list[XueqiuStockQuoteTags]] = None


def filter_dict_by_dataclass(cls, d):
    return {k: v for k, v in d.items() if k in cls.__annotations__}


def xueqiu_stock_quote_from_dict(data: dict) -> XueqiuStockQuote:
    return XueqiuStockQuote(
        market=XueqiuStockQuoteMarket(
            **filter_dict_by_dataclass(XueqiuStockQuoteMarket, data["market"])
        ),
        quote=XueqiuStockQuoteQuote(
            **filter_dict_by_dataclass(XueqiuStockQuoteQuote, data["quote"])
        ),
        others=XueqiuStockQuoteOthers(
            **filter_dict_by_dataclass(XueqiuStockQuoteOthers, data["others"])
        ),
        tags=[
            XueqiuStockQuoteTags(**filter_dict_by_dataclass(XueqiuStockQuoteTags, tag))
            for tag in data["tags"]
        ],
    )
