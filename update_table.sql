DROP TABLE ticker_indicator;

-- 创建 ticker_indicator 表
CREATE TABLE IF NOT EXISTS ticker_indicator (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER NOT NULL,
    indicator_key VARCHAR(50) NOT NULL,  -- 从 indicator_id 改名为 indicator_key
    kl_type VARCHAR(20) NOT NULL,
    time_key VARCHAR(20) NOT NULL,
    history TEXT,  -- JSON 格式存储历史数据
    status INTEGER DEFAULT 1,
    code VARCHAR(20),
    version INTEGER DEFAULT 1,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (ticker_id, indicator_key, kl_type)  -- 添加唯一约束，确保不会有重复记录
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_ticker_indicator_ticker_id ON ticker_indicator(ticker_id);
CREATE INDEX IF NOT EXISTS idx_ticker_indicator_keys ON ticker_indicator(indicator_key, kl_type);
