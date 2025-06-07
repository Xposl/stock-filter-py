-- 数据库更新脚本：移除外键约束和更新表结构
-- 适用于 MySQL 和 SQLite

-- MySQL 版本更新脚本
-- 移除news_articles表的外键约束
SET foreign_key_checks = 0;

-- 检查并删除外键约束（如果存在）
ALTER TABLE news_articles DROP FOREIGN KEY IF EXISTS `news_articles_ibfk_1`;
ALTER TABLE news_articles DROP FOREIGN KEY IF EXISTS `fk_news_articles_source_id`;

-- 重新启用外键检查
SET foreign_key_checks = 1;

-- 创建market表（如果不存在）
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

-- 添加market表索引
CREATE INDEX IF NOT EXISTS idx_market_code ON market(code);
CREATE INDEX IF NOT EXISTS idx_market_status ON market(status);

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

-- 更新ticker表：移除K线相关字段（如果存在）
-- 注意：这会删除数据，请在执行前备份
ALTER TABLE ticker 
DROP COLUMN IF EXISTS time_key,
DROP COLUMN IF EXISTS open,
DROP COLUMN IF EXISTS close,
DROP COLUMN IF EXISTS high,
DROP COLUMN IF EXISTS low,
DROP COLUMN IF EXISTS volume,
DROP COLUMN IF EXISTS turnover,
DROP COLUMN IF EXISTS turnover_rate;

-- SQLite 版本更新脚本（由于SQLite不支持DROP FOREIGN KEY，需要重建表）
-- 以下注释的脚本适用于SQLite数据库

/*
-- SQLite 更新脚本（需要手动执行）

-- 1. 创建新的news_articles表（没有外键约束）
CREATE TABLE IF NOT EXISTS news_articles_new (
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
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 2. 复制数据
INSERT INTO news_articles_new SELECT * FROM news_articles;

-- 3. 删除旧表
DROP TABLE news_articles;

-- 4. 重命名新表
ALTER TABLE news_articles_new RENAME TO news_articles;

-- 5. 重新创建索引
CREATE INDEX idx_news_articles_title ON news_articles(title);
CREATE INDEX idx_news_articles_url ON news_articles(url);
CREATE INDEX idx_news_articles_url_hash ON news_articles(url_hash);
CREATE INDEX idx_news_articles_source_id ON news_articles(source_id);
CREATE INDEX idx_news_articles_status ON news_articles(status);
CREATE INDEX idx_news_articles_published_at ON news_articles(published_at);
CREATE INDEX idx_news_articles_crawled_at ON news_articles(crawled_at);

-- 6. 创建market表
CREATE TABLE IF NOT EXISTS market (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  region TEXT NOT NULL,
  currency TEXT DEFAULT 'USD',
  timezone TEXT NOT NULL,
  open_time TEXT NOT NULL,
  close_time TEXT NOT NULL,
  trading_days TEXT DEFAULT 'Mon,Tue,Wed,Thu,Fri',
  status INTEGER DEFAULT 1,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 7. 插入默认市场数据
INSERT OR REPLACE INTO market (id, code, name, region, currency, timezone, open_time, close_time, trading_days, status) VALUES
(1, 'HK', '香港交易所', 'Hong Kong', 'HKD', 'Asia/Hong_Kong', '09:30', '16:00', 'Mon,Tue,Wed,Thu,Fri', 1),
(2, 'ZH', 'A股市场', 'China', 'CNY', 'Asia/Shanghai', '09:30', '15:00', 'Mon,Tue,Wed,Thu,Fri', 1),
(3, 'US', '美国股市', 'United States', 'USD', 'America/New_York', '09:30', '16:00', 'Mon,Tue,Wed,Thu,Fri', 1);

-- 8. 为ticker表重建（移除K线字段）
CREATE TABLE IF NOT EXISTS ticker_new (
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
  update_date TEXT DEFAULT NULL,
  listed_date TEXT DEFAULT NULL,
  create_time TEXT DEFAULT CURRENT_TIMESTAMP,
  version INTEGER DEFAULT 1,
  UNIQUE (code)
);

-- 9. 复制ticker数据（排除K线字段）
INSERT INTO ticker_new (id, code, name, group_id, type, source, status, is_deleted, remark, 
                       pe_forecast, pettm, pb, total_share, lot_size, update_date, listed_date, 
                       create_time, version)
SELECT id, code, name, group_id, type, source, status, is_deleted, remark, 
       pe_forecast, pettm, pb, total_share, lot_size, update_date, listed_date, 
       create_time, version 
FROM ticker;

-- 10. 删除旧ticker表并重命名
DROP TABLE ticker;
ALTER TABLE ticker_new RENAME TO ticker;

-- 11. 重新创建ticker索引
CREATE INDEX idx_ticker_code ON ticker(code);
CREATE INDEX idx_ticker_name ON ticker(name);
CREATE INDEX idx_ticker_group_id ON ticker(group_id);
CREATE INDEX idx_ticker_status ON ticker(status);
*/ 