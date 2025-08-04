-- 数据缓存优化任务 - 数据库迁移脚本
-- 创建时间: 2025-08-02
-- 目标: 优化ticker_score表结构，支持智能缓存机制

-- Step 1: 添加 analysis_data 字段用于存储分析数据
ALTER TABLE ticker_score ADD COLUMN analysis_data JSON COMMENT '存储分析数据（如raw_score, z_score, trend_strength等）';

-- Step 2: 添加缓存相关字段
ALTER TABLE ticker_score ADD COLUMN cache_version INT DEFAULT 1 COMMENT '缓存版本号';
ALTER TABLE ticker_score ADD COLUMN last_kline_time VARCHAR(20) COMMENT '最新K线数据时间';
ALTER TABLE ticker_score ADD COLUMN next_update_time DATETIME COMMENT '下次更新时间';

-- Step 3: 创建复合索引提高查询性能（仅当索引不存在时创建）
CREATE INDEX IF NOT EXISTS idx_ticker_score_ticker_time ON ticker_score(ticker_id, time_key);
-- idx_ticker_score_time_key 已存在，跳过创建
CREATE INDEX IF NOT EXISTS idx_ticker_score_cache ON ticker_score(ticker_id, last_kline_time, next_update_time);

-- Step 4: 数据迁移 - 将现有history数据迁移到analysis_data
-- 注意：运行此脚本前请先备份数据库

-- 4.1 检查数据完整性
SELECT 
    COUNT(*) as total_records,
    COUNT(history) as records_with_history,
    COUNT(CASE WHEN history IS NOT NULL AND history != '' THEN 1 END) as non_empty_history
FROM ticker_score;

-- 4.2 迁移数据 - 将history字段中的分析数据转移到analysis_data
UPDATE ticker_score 
SET analysis_data = 
    CASE 
        WHEN history IS NOT NULL AND history != '' AND history != 'null' THEN
            CASE 
                WHEN history LIKE '{"raw_score%' OR history LIKE '{"z_score%' THEN
                    CAST(history AS JSON)
                ELSE
                    JSON_OBJECT('legacy_data', history)
                END
        ELSE
            NULL
    END
WHERE history IS NOT NULL AND history != '' AND history != 'null';

-- 4.3 验证迁移结果
SELECT 
    COUNT(*) as total_records,
    COUNT(analysis_data) as records_with_analysis_data,
    COUNT(CASE WHEN analysis_data IS NOT NULL THEN 1 END) as non_empty_analysis_data
FROM ticker_score;

-- Step 5: 清空history字段，准备用于存储历史评分数组
-- 注意：仅当确认数据已成功迁移到analysis_data后执行
-- UPDATE ticker_score SET history = NULL WHERE analysis_data IS NOT NULL;

-- Step 6: 创建历史数据表（可选，用于分离历史数据）
CREATE TABLE IF NOT EXISTS ticker_score_history (
    id INT NOT NULL AUTO_INCREMENT,
    ticker_id INT NOT NULL,
    time_key VARCHAR(20) NOT NULL,
    score FLOAT DEFAULT 0,
    analysis_data JSON,
    cache_version INT DEFAULT 1,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_ticker_history (ticker_id, time_key),
    INDEX idx_ticker_time (ticker_id, create_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- Step 7: 创建缓存状态表（可选，用于高级缓存管理）
CREATE TABLE IF NOT EXISTS ticker_cache_status (
    ticker_id INT NOT NULL PRIMARY KEY,
    last_score_time VARCHAR(20),
    last_kline_time VARCHAR(20),
    next_update_time DATETIME,
    cache_version INT DEFAULT 1,
    update_count INT DEFAULT 0,
    last_update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_next_update (next_update_time),
    INDEX idx_cache_version (cache_version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

-- Step 8: 创建触发器自动维护缓存状态
DELIMITER //
CREATE TRIGGER update_cache_status_after_score_insert
AFTER INSERT ON ticker_score
FOR EACH ROW
BEGIN
    INSERT INTO ticker_cache_status (ticker_id, last_score_time, last_kline_time, next_update_time, cache_version, update_count)
    VALUES (NEW.ticker_id, NEW.time_key, NEW.last_kline_time, NEW.next_update_time, NEW.cache_version, 1)
    ON DUPLICATE KEY UPDATE
        last_score_time = NEW.time_key,
        last_kline_time = NEW.last_kline_time,
        next_update_time = NEW.next_update_time,
        cache_version = NEW.cache_version,
        update_count = update_count + 1;
END//

CREATE TRIGGER update_cache_status_after_score_update
AFTER UPDATE ON ticker_score
FOR EACH ROW
BEGIN
    UPDATE ticker_cache_status 
    SET 
        last_score_time = NEW.time_key,
        last_kline_time = NEW.last_kline_time,
        next_update_time = NEW.next_update_time,
        cache_version = NEW.cache_version,
        update_count = update_count + 1,
        last_update_time = NOW()
    WHERE ticker_id = NEW.ticker_id;
END//
DELIMITER ;

-- Step 9: 回滚脚本（在需要时使用）
-- 如果需要回滚，请按以下顺序执行：
-- 1. DROP TRIGGER IF EXISTS update_cache_status_after_score_insert;
-- 2. DROP TRIGGER IF EXISTS update_cache_status_after_score_update;
-- 3. DROP TABLE IF EXISTS ticker_cache_status;
-- 4. DROP TABLE IF EXISTS ticker_score_history;
-- 5. ALTER TABLE ticker_score DROP COLUMN IF EXISTS analysis_data;
-- 6. ALTER TABLE ticker_score DROP COLUMN IF EXISTS cache_version;
-- 7. ALTER TABLE ticker_score DROP COLUMN IF EXISTS last_kline_time;
-- 8. ALTER TABLE ticker_score DROP COLUMN IF EXISTS next_update_time;
-- 9. DROP INDEX idx_ticker_score_ticker_time ON ticker_score;
-- 10. DROP INDEX idx_ticker_score_analysis ON ticker_score;
-- 11. DROP INDEX idx_ticker_score_cache ON ticker_score;

-- 注意：实际迁移时请根据情况选择执行的步骤