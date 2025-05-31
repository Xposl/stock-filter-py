-- SQLite 版本 SQL 初始化脚本

-- 删除已存在的表
DROP TABLE IF EXISTS news_articles;
DROP TABLE IF EXISTS news_sources;
DROP TABLE IF EXISTS ticker_indicator;
DROP TABLE IF EXISTS ticker_strategy;
DROP TABLE IF EXISTS ticker_score;
DROP TABLE IF EXISTS ticker_valuation;
DROP TABLE IF EXISTS ticker;
DROP TABLE IF EXISTS valuation;
DROP TABLE IF EXISTS api_log;

-- 创建 ticker 表（股票信息主表）
CREATE TABLE IF NOT EXISTS ticker (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT NOT NULL,
  name TEXT NOT NULL,
  group_id INTEGER DEFAULT 0,
  type INTEGER DEFAULT 1,
  source INTEGER DEFAULT 1,
  status INTEGER DEFAULT 1,
  is_deleted INTEGER DEFAULT 0,
  remark TEXT,
  pe_forecast REAL DEFAULT NULL,
  pettm REAL DEFAULT NULL,
  pb REAL DEFAULT NULL,
  total_share REAL DEFAULT NULL,
  lot_size INTEGER DEFAULT 100,
  time_key TEXT DEFAULT NULL,
  open REAL DEFAULT NULL,
  close REAL DEFAULT NULL,
  high REAL DEFAULT NULL,
  low REAL DEFAULT NULL,
  volume REAL DEFAULT NULL,
  turnover REAL DEFAULT NULL,
  turnover_rate REAL DEFAULT NULL,
  update_date TEXT DEFAULT NULL,
  listed_date TEXT DEFAULT NULL,
  create_time TEXT DEFAULT CURRENT_TIMESTAMP,
  version INTEGER DEFAULT 1,
  UNIQUE (code)
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_ticker_code ON ticker(code);
CREATE INDEX IF NOT EXISTS idx_ticker_name ON ticker(name);
CREATE INDEX IF NOT EXISTS idx_ticker_group_id ON ticker(group_id);
CREATE INDEX IF NOT EXISTS idx_ticker_status ON ticker(status);

-- 创建 ticker_indicator 表
CREATE TABLE IF NOT EXISTS ticker_indicator (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER NOT NULL,
    indicator_key TEXT NOT NULL,
    kl_type TEXT NOT NULL,
    time_key TEXT NOT NULL,
    history TEXT,  -- JSON 格式存储历史数据
    status INTEGER DEFAULT 1,
    code TEXT,
    version INTEGER DEFAULT 1,
    create_time TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (ticker_id, indicator_key, kl_type)  -- 添加唯一约束，确保不会有重复记录
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_ticker_indicator_ticker_id ON ticker_indicator(ticker_id);
CREATE INDEX IF NOT EXISTS idx_ticker_indicator_keys ON ticker_indicator(indicator_key, kl_type);

-- 创建 ticker_strategy 表
CREATE TABLE IF NOT EXISTS ticker_strategy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER NOT NULL,
    strategy_key TEXT NOT NULL,
    kl_type TEXT NOT NULL,
    time_key TEXT NOT NULL,
    data TEXT,  -- JSON 格式存储策略数据
    pos_data TEXT,  -- JSON 格式存储持仓数据
    status INTEGER DEFAULT 1,
    code TEXT,
    version INTEGER DEFAULT 1,
    create_time TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (ticker_id, strategy_key, kl_type)  -- 添加唯一约束，确保不会有重复记录
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_ticker_strategy_ticker_id ON ticker_strategy(ticker_id);
CREATE INDEX IF NOT EXISTS idx_ticker_strategy_keys ON ticker_strategy(strategy_key, kl_type);

-- 创建 ticker_valuation 表
CREATE TABLE IF NOT EXISTS ticker_valuation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER NOT NULL,
    valuation_key TEXT NOT NULL,
    time_key TEXT NOT NULL,
    target_price REAL DEFAULT -1,  -- 平均目标价
    max_target_price REAL DEFAULT -1,  -- 最高目标价
    min_target_price REAL DEFAULT -1,  -- 最低目标价
    remark TEXT,  -- 备注信息
    status INTEGER DEFAULT 1,
    code TEXT,
    version INTEGER DEFAULT 1,
    create_time TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (ticker_id, valuation_key)  -- 添加唯一约束，确保不会有重复记录
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_ticker_valuation_ticker_id ON ticker_valuation(ticker_id);
CREATE INDEX IF NOT EXISTS idx_ticker_valuation_key ON ticker_valuation(valuation_key);

-- 创建 ticker_score 表
CREATE TABLE IF NOT EXISTS ticker_score (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER NOT NULL,
    time_key TEXT NOT NULL,
    ma_buy REAL DEFAULT 0,
    ma_sell REAL DEFAULT 0,
    ma_score REAL DEFAULT 0,
    in_buy REAL DEFAULT 0,
    in_sell REAL DEFAULT 0,
    in_score REAL DEFAULT 0,
    strategy_buy REAL DEFAULT 0,
    strategy_sell REAL DEFAULT 0,
    strategy_score REAL DEFAULT 0,
    score REAL DEFAULT 0,
    status INTEGER DEFAULT 1,
    history TEXT,  -- JSON 格式存储历史数据
    create_time TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_ticker_score_ticker_id ON ticker_score(ticker_id);
CREATE INDEX IF NOT EXISTS idx_ticker_score_time_key ON ticker_score(time_key);

-- 创建 api_log 表
CREATE TABLE IF NOT EXISTS api_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  path TEXT NOT NULL,
  method TEXT NOT NULL,
  params TEXT,
  exception TEXT,
  traceback TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 创建新闻源表
CREATE TABLE IF NOT EXISTS news_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    source_type TEXT NOT NULL,
    url TEXT NOT NULL,
    api_key TEXT,
    update_frequency INTEGER DEFAULT 3600,
    max_articles_per_fetch INTEGER DEFAULT 50,
    filter_keywords TEXT,
    filter_categories TEXT,
    language TEXT DEFAULT 'zh',
    region TEXT DEFAULT 'CN',
    status TEXT DEFAULT 'active',
    last_fetch_time TEXT,
    last_error_message TEXT,
    total_articles_fetched INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 创建新闻文章表
CREATE TABLE IF NOT EXISTS news_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    url_hash TEXT NOT NULL UNIQUE,
    content TEXT,
    summary TEXT,
    author TEXT,
    source_id INTEGER NOT NULL,
    source_name TEXT,
    category TEXT,
    published_at TEXT,
    crawled_at TEXT DEFAULT CURRENT_TIMESTAMP,
    language TEXT DEFAULT 'zh',
    region TEXT DEFAULT 'CN',
    entities TEXT,
    keywords TEXT,
    sentiment_score REAL,
    topics TEXT,
    importance_score REAL DEFAULT 0.0,
    market_relevance_score REAL DEFAULT 0.0,
    status TEXT DEFAULT 'pending',
    processed_at TEXT,
    error_message TEXT,
    word_count INTEGER DEFAULT 0,
    read_time_minutes INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES news_sources(id)
);

-- 创建新闻相关索引
CREATE INDEX IF NOT EXISTS idx_news_sources_name ON news_sources(name);
CREATE INDEX IF NOT EXISTS idx_news_sources_status ON news_sources(status);
CREATE INDEX IF NOT EXISTS idx_news_sources_type ON news_sources(source_type);

CREATE INDEX IF NOT EXISTS idx_news_articles_title ON news_articles(title);
CREATE INDEX IF NOT EXISTS idx_news_articles_url ON news_articles(url);
CREATE INDEX IF NOT EXISTS idx_news_articles_url_hash ON news_articles(url_hash);
CREATE INDEX IF NOT EXISTS idx_news_articles_source_id ON news_articles(source_id);
CREATE INDEX IF NOT EXISTS idx_news_articles_status ON news_articles(status);
CREATE INDEX IF NOT EXISTS idx_news_articles_published_at ON news_articles(published_at);
CREATE INDEX IF NOT EXISTS idx_news_articles_crawled_at ON news_articles(crawled_at);
