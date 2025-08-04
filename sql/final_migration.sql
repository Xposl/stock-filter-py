-- 数据缓存优化最终迁移脚本
-- 执行顺序：
-- 1. 先运行此SQL脚本
-- 2. 然后运行 Python 迁移脚本: python scripts/migrate_ticker_score_data.py

-- Step 1: 添加新字段到ticker_score表
ALTER TABLE ticker_score 
ADD COLUMN analysis_data TEXT COMMENT '存储分析数据（JSON格式）',
ADD COLUMN cache_version INT DEFAULT 1 COMMENT '缓存版本号',
ADD COLUMN last_kline_time VARCHAR(20) COMMENT '最新K线数据时间',
ADD COLUMN next_update_time DATETIME COMMENT '下次更新时间';

-- Step 2: 优化索引
CREATE INDEX IF NOT EXISTS idx_ticker_score_ticker_time ON ticker_score(ticker_id, time_key);
CREATE INDEX IF NOT EXISTS idx_ticker_score_cache ON ticker_score(ticker_id, last_kline_time, next_update_time);

-- Step 3: 数据迁移将在Python脚本中完成
-- 完成后可运行以下验证查询：

-- 验证迁移结果
SELECT 
    COUNT(*) as total_records,
    COUNT(analysis_data) as records_with_analysis_data,
    COUNT(CASE WHEN analysis_data IS NOT NULL THEN 1 END) as non_empty_analysis_data,
    COUNT(CASE WHEN cache_version IS NOT NULL THEN 1 END) as records_with_cache_version
FROM ticker_score;

-- 检查数据示例
SELECT 
    id,
    ticker_id,
    time_key,
    score,
    analysis_data,
    cache_version,
    last_kline_time,
    next_update_time
FROM ticker_score 
WHERE analysis_data IS NOT NULL 
LIMIT 5;