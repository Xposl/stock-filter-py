#!/bin/bash

# InvestNote 新闻抓取 Cron 任务脚本
# 用于系统级别的定时新闻抓取

# 配置变量
API_BASE_URL="http://localhost:8000/investnote"
LOG_DIR="/var/log/investnote"
LOG_FILE="$LOG_DIR/news_fetch.log"

# 创建日志目录（如果不存在）
mkdir -p "$LOG_DIR"

# 获取当前时间戳
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# 日志函数
log() {
    echo "[$TIMESTAMP] $1" >> "$LOG_FILE"
}

# 发送HTTP请求的函数
send_request() {
    local endpoint=$1
    local method=${2:-GET}
    local data=${3:-""}
    
    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        curl -s -X POST \
             -H "Content-Type: application/json" \
             -d "$data" \
             "$API_BASE_URL$endpoint"
    elif [ "$method" = "POST" ]; then
        curl -s -X POST \
             -H "Content-Type: application/json" \
             "$API_BASE_URL$endpoint"
    else
        curl -s "$API_BASE_URL$endpoint"
    fi
}

# 检查API服务是否可用
check_api_health() {
    log "检查API服务健康状态..."
    
    response=$(send_request "/")
    if [ $? -eq 0 ] && echo "$response" | grep -q "InvestNote API Service"; then
        log "✅ API服务正常"
        return 0
    else
        log "❌ API服务不可用"
        return 1
    fi
}

# 触发新闻抓取
trigger_news_fetch() {
    log "触发新闻抓取任务..."
    
    # 发送POST请求到新闻抓取端点
    response=$(send_request "/cron/news" "POST" '{"limit": 100}')
    
    if [ $? -eq 0 ]; then
        # 解析响应状态
        if echo "$response" | grep -q '"status": "success"'; then
            log "✅ 新闻抓取任务触发成功"
            log "响应: $response"
        else
            log "❌ 新闻抓取任务触发失败"
            log "响应: $response"
            return 1
        fi
    else
        log "❌ 无法连接到新闻抓取API"
        return 1
    fi
}

# 获取新闻抓取状态
get_fetch_status() {
    log "获取新闻抓取状态..."
    
    response=$(send_request "/cron/news/status")
    
    if [ $? -eq 0 ]; then
        log "📊 抓取状态: $response"
    else
        log "❌ 无法获取抓取状态"
    fi
}

# 主函数
main() {
    log "========== 开始新闻抓取定时任务 =========="
    
    # 检查API健康状态
    if ! check_api_health; then
        log "❌ API服务不可用，跳过新闻抓取"
        exit 1
    fi
    
    # 触发新闻抓取
    if trigger_news_fetch; then
        # 等待一段时间后获取状态
        sleep 5
        get_fetch_status
        log "✅ 新闻抓取定时任务完成"
    else
        log "❌ 新闻抓取定时任务失败"
        exit 1
    fi
    
    log "========== 新闻抓取定时任务结束 =========="
}

# 脚本入口
case "${1:-main}" in
    "health")
        check_api_health
        ;;
    "fetch")
        trigger_news_fetch
        ;;
    "status")
        get_fetch_status
        ;;
    "main"|*)
        main
        ;;
esac 