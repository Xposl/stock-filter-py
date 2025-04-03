DROP TABLE IF EXISTS ticker_indicator;
DROP TABLE IF EXISTS ticker_strategy;
DROP TABLE IF EXISTS ticker_score;
DROP TABLE IF EXISTS ticker_valuation;
DROP TABLE IF EXISTS valuation;

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

-- 创建 ticker_strategy 表
CREATE TABLE IF NOT EXISTS ticker_strategy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER NOT NULL,
    strategy_key VARCHAR(50) NOT NULL,  -- 从 strategy_id 改名为 strategy_key，直接使用Strategy的getKey值
    kl_type VARCHAR(20) NOT NULL,
    time_key VARCHAR(20) NOT NULL,
    data TEXT,  -- JSON 格式存储策略数据
    pos_data TEXT,  -- JSON 格式存储持仓数据
    status INTEGER DEFAULT 1,
    code VARCHAR(20),
    version INTEGER DEFAULT 1,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (ticker_id, strategy_key, kl_type)  -- 添加唯一约束，确保不会有重复记录
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_ticker_strategy_ticker_id ON ticker_strategy(ticker_id);
CREATE INDEX IF NOT EXISTS idx_ticker_strategy_keys ON ticker_strategy(strategy_key, kl_type);

-- 创建 ticker_valuation 表
CREATE TABLE IF NOT EXISTS ticker_valuation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER NOT NULL,
    valuation_key VARCHAR(50) NOT NULL,  -- 直接使用 Valuation 的 getKey 值
    time_key VARCHAR(20) NOT NULL,
    target_price REAL DEFAULT -1,  -- 平均目标价
    max_target_price REAL DEFAULT -1,  -- 最高目标价
    min_target_price REAL DEFAULT -1,  -- 最低目标价
    remark TEXT,  -- 备注信息
    status INTEGER DEFAULT 1,
    code VARCHAR(20),
    version INTEGER DEFAULT 1,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (ticker_id, valuation_key)  -- 添加唯一约束，确保不会有重复记录
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_ticker_valuation_ticker_id ON ticker_valuation(ticker_id);
CREATE INDEX IF NOT EXISTS idx_ticker_valuation_key ON ticker_valuation(valuation_key);

-- 创建 ticker_score 表
CREATE TABLE IF NOT EXISTS ticker_score (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER NOT NULL,
    time_key VARCHAR(20) NOT NULL,
    ma_buy INTEGER DEFAULT 0,
    ma_sell INTEGER DEFAULT 0,
    ma_score FLOAT DEFAULT 0,
    in_buy INTEGER DEFAULT 0,
    in_sell INTEGER DEFAULT 0,
    in_score FLOAT DEFAULT 0,
    strategy_buy INTEGER DEFAULT 0,
    strategy_sell INTEGER DEFAULT 0,
    strategy_score FLOAT DEFAULT 0,
    score FLOAT DEFAULT 0,
    status INTEGER DEFAULT 1,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_ticker_score_ticker_id ON ticker_score(ticker_id);
CREATE INDEX IF NOT EXISTS idx_ticker_score_time_key ON ticker_score(time_key);
