-- MySQL 8.0 版本 SQL 初始化脚本

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
DROP TABLE IF EXISTS market;

-- 创建 market 表（市场信息表）
CREATE TABLE IF NOT EXISTS market (
  id INT NOT NULL AUTO_INCREMENT,
  code VARCHAR(10) NOT NULL UNIQUE,
  name VARCHAR(100) NOT NULL,
  region VARCHAR(50) NOT NULL,
  currency VARCHAR(10) DEFAULT 'USD',
  timezone VARCHAR(50) NOT NULL,
  open_time TIME NOT NULL,
  close_time TIME NOT NULL,
  trading_days VARCHAR(100) DEFAULT 'Mon,Tue,Wed,Thu,Fri',
  status INT DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建 ticker 表（股票信息主表）
CREATE TABLE IF NOT EXISTS ticker (
  id INT NOT NULL AUTO_INCREMENT,
  code VARCHAR(20) NOT NULL,
  name VARCHAR(100) NOT NULL,
  group_id INT DEFAULT 0,
  type INT DEFAULT 1,
  source INT DEFAULT 1,
  status INT DEFAULT 1,
  is_deleted TINYINT(1) DEFAULT 0,
  remark TEXT,
  pe_forecast DOUBLE DEFAULT NULL,
  pettm DOUBLE DEFAULT NULL,
  pb DOUBLE DEFAULT NULL,
  total_share DOUBLE DEFAULT NULL,
  lot_size INT DEFAULT 100,
  update_date DATETIME DEFAULT NULL,
  listed_date DATETIME DEFAULT NULL,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  version INT DEFAULT 1,
  PRIMARY KEY (id),
  UNIQUE KEY (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- 创建索引以提高查询性能
CREATE INDEX idx_ticker_code ON ticker(code);
CREATE INDEX idx_ticker_name ON ticker(name);
CREATE INDEX idx_ticker_group_id ON ticker(group_id);
CREATE INDEX idx_ticker_status ON ticker(status);

-- 创建 ticker_indicator 表
CREATE TABLE IF NOT EXISTS ticker_indicator (
    id INT NOT NULL AUTO_INCREMENT,
    ticker_id INT NOT NULL,
    indicator_key VARCHAR(50) NOT NULL,
    kl_type VARCHAR(20) NOT NULL,
    time_key VARCHAR(20) NOT NULL,
    history TEXT,  -- JSON 格式存储历史数据
    status INT DEFAULT 1,
    code VARCHAR(20),
    version INT DEFAULT 1,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY (ticker_id, indicator_key, kl_type)  -- 添加唯一约束，确保不会有重复记录
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- 创建索引以提高查询性能
CREATE INDEX idx_ticker_indicator_ticker_id ON ticker_indicator(ticker_id);
CREATE INDEX idx_ticker_indicator_keys ON ticker_indicator(indicator_key, kl_type);

-- 创建 ticker_strategy 表
CREATE TABLE IF NOT EXISTS ticker_strategy (
    id INT NOT NULL AUTO_INCREMENT,
    ticker_id INT NOT NULL,
    strategy_key VARCHAR(50) NOT NULL,
    kl_type VARCHAR(20) NOT NULL,
    time_key VARCHAR(20) NOT NULL,
    data TEXT,  -- JSON 格式存储策略数据
    pos_data TEXT,  -- JSON 格式存储持仓数据
    status INT DEFAULT 1,
    code VARCHAR(20),
    version INT DEFAULT 1,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY (ticker_id, strategy_key, kl_type)  -- 添加唯一约束，确保不会有重复记录
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- 创建索引以提高查询性能
CREATE INDEX idx_ticker_strategy_ticker_id ON ticker_strategy(ticker_id);
CREATE INDEX idx_ticker_strategy_keys ON ticker_strategy(strategy_key, kl_type);

-- 创建 ticker_valuation 表
CREATE TABLE IF NOT EXISTS ticker_valuation (
    id INT NOT NULL AUTO_INCREMENT,
    ticker_id INT NOT NULL,
    valuation_key VARCHAR(50) NOT NULL,
    time_key VARCHAR(20) NOT NULL,
    target_price DOUBLE DEFAULT -1,  -- 平均目标价
    max_target_price DOUBLE DEFAULT -1,  -- 最高目标价
    min_target_price DOUBLE DEFAULT -1,  -- 最低目标价
    remark TEXT,  -- 备注信息
    status INT DEFAULT 1,
    code VARCHAR(20),
    version INT DEFAULT 1,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY (ticker_id, valuation_key)  -- 添加唯一约束，确保不会有重复记录
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- 创建索引以提高查询性能
CREATE INDEX idx_ticker_valuation_ticker_id ON ticker_valuation(ticker_id);
CREATE INDEX idx_ticker_valuation_key ON ticker_valuation(valuation_key);

-- 创建 ticker_score 表
CREATE TABLE IF NOT EXISTS ticker_score (
    id INT NOT NULL AUTO_INCREMENT,
    ticker_id INT NOT NULL,
    time_key VARCHAR(20) NOT NULL,
    ma_buy FLOAT DEFAULT 0,
    ma_sell FLOAT DEFAULT 0,
    ma_score FLOAT DEFAULT 0,
    in_buy FLOAT DEFAULT 0,
    in_sell FLOAT DEFAULT 0,
    in_score FLOAT DEFAULT 0,
    strategy_buy FLOAT DEFAULT 0,
    strategy_sell FLOAT DEFAULT 0,
    strategy_score FLOAT DEFAULT 0,
    score FLOAT DEFAULT 0,
    status INT DEFAULT 1,
    history TEXT,  -- JSON 格式存储历史数据
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- 创建索引以提高查询性能
CREATE INDEX idx_ticker_score_ticker_id ON ticker_score(ticker_id);
CREATE INDEX idx_ticker_score_time_key ON ticker_score(time_key);

-- 创建 api_log 表
CREATE TABLE IF NOT EXISTS api_log (
  id INT NOT NULL AUTO_INCREMENT,
  path VARCHAR(255) NOT NULL,
  method VARCHAR(10) NOT NULL,
  params TEXT,
  exception TEXT,
  traceback TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- 创建新闻源表（无外键约束）
CREATE TABLE IF NOT EXISTS news_sources (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    source_type ENUM('rss', 'api', 'website', 'twitter') NOT NULL,
    url VARCHAR(2048) NOT NULL,
    api_key VARCHAR(512),
    update_frequency INT DEFAULT 3600,
    max_articles_per_fetch INT DEFAULT 50,
    filter_keywords TEXT,
    filter_categories TEXT,
    language VARCHAR(10) DEFAULT 'zh',
    region VARCHAR(10) DEFAULT 'CN',
    status ENUM('active', 'inactive', 'error', 'suspended') DEFAULT 'active',
    last_fetch_time DATETIME,
    last_error_message TEXT,
    total_articles_fetched INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建新闻文章表（无外键约束）
CREATE TABLE IF NOT EXISTS news_articles (
    id INT NOT NULL AUTO_INCREMENT,
    title VARCHAR(1024) NOT NULL,
    url VARCHAR(2048) NOT NULL,
    url_hash VARCHAR(64) NOT NULL UNIQUE,
    content LONGTEXT,
    summary TEXT,
    author VARCHAR(255),
    source_id INT NOT NULL,
    source_name VARCHAR(255),
    category VARCHAR(100),
    published_at DATETIME,
    crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    language VARCHAR(10) DEFAULT 'zh',
    region VARCHAR(10) DEFAULT 'CN',
    entities TEXT,
    keywords TEXT,
    sentiment_score FLOAT,
    topics TEXT,
    importance_score FLOAT DEFAULT 0.0,
    market_relevance_score FLOAT DEFAULT 0.0,
    status ENUM('pending', 'processing', 'processed', 'failed', 'archived') DEFAULT 'pending',
    processed_at DATETIME,
    error_message TEXT,
    word_count INT DEFAULT 0,
    read_time_minutes INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建市场表索引
CREATE INDEX idx_market_code ON market(code);
CREATE INDEX idx_market_status ON market(status);

-- 创建新闻相关索引
CREATE INDEX idx_news_sources_name ON news_sources(name);
CREATE INDEX idx_news_sources_status ON news_sources(status);
CREATE INDEX idx_news_sources_type ON news_sources(source_type);

CREATE INDEX idx_news_articles_title ON news_articles(title(255));
CREATE INDEX idx_news_articles_url ON news_articles(url(255));
CREATE INDEX idx_news_articles_url_hash ON news_articles(url_hash);
CREATE INDEX idx_news_articles_source_id ON news_articles(source_id);
CREATE INDEX idx_news_articles_status ON news_articles(status);
CREATE INDEX idx_news_articles_published_at ON news_articles(published_at);
CREATE INDEX idx_news_articles_crawled_at ON news_articles(crawled_at);

-- 插入默认市场数据
INSERT INTO market (id, code, name, region, currency, timezone, open_time, close_time, trading_days, status) VALUES
(1, 'HK', '香港交易所', 'Hong Kong', 'HKD', 'Asia/Hong_Kong', '09:30:00', '16:00:00', 'Mon,Tue,Wed,Thu,Fri', 1),
(2, 'ZH', 'A股市场', 'China', 'CNY', 'Asia/Shanghai', '09:30:00', '15:00:00', 'Mon,Tue,Wed,Thu,Fri', 1),
(3, 'US', '美国股市', 'United States', 'USD', 'America/New_York', '09:30:00', '16:00:00', 'Mon,Tue,Wed,Thu,Fri', 1)
ON DUPLICATE KEY UPDATE 
name=VALUES(name), 
region=VALUES(region), 
currency=VALUES(currency), 
timezone=VALUES(timezone), 
open_time=VALUES(open_time), 
close_time=VALUES(close_time), 
trading_days=VALUES(trading_days), 
status=VALUES(status);
