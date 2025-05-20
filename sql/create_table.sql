-- MySQL 8.0 版本 SQL 初始化脚本

-- 删除已存在的表
DROP TABLE IF EXISTS ticker_indicator;
DROP TABLE IF EXISTS ticker_strategy;
DROP TABLE IF EXISTS ticker_score;
DROP TABLE IF EXISTS ticker_valuation;
DROP TABLE IF EXISTS ticker;
DROP TABLE IF EXISTS valuation;
DROP TABLE IF EXISTS api_log;

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
  time_key VARCHAR(20) DEFAULT NULL,
  open DOUBLE DEFAULT NULL,
  close DOUBLE DEFAULT NULL,
  high DOUBLE DEFAULT NULL,
  low DOUBLE DEFAULT NULL,
  volume DOUBLE DEFAULT NULL,
  turnover DOUBLE DEFAULT NULL,
  turnover_rate DOUBLE DEFAULT NULL,
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
