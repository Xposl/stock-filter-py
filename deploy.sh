#!/bin/bash

# 设置变量
IMAGE_VERSION=$1
if [ -z "$IMAGE_VERSION" ]; then
  echo "请提供镜像版本号"
  echo "用法: ./deploy.sh <版本号>"
  exit 1
fi

echo "🚀 开始部署InvestNote-py版本: ${IMAGE_VERSION}"

# 磁盘空间检查和清理
echo "💾 检查磁盘空间..."
AVAILABLE_SPACE=$(df / | awk 'NR==2 {print $4}')
REQUIRED_SPACE=5368709120  # 5GB in bytes

if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
    echo "⚠️  磁盘空间不足，开始清理Docker资源..."
    
    # 停止所有容器
    echo "🛑 停止所有运行中的容器..."
    docker stop $(docker ps -q) 2>/dev/null || true
    
    # 清理未使用的Docker资源
    echo "🧹 清理未使用的Docker镜像、容器和卷..."
    docker system prune -f
    
    # 清理未使用的镜像（包括未标记的镜像）
    echo "🗑️  清理未使用的镜像..."
    docker image prune -a -f
    
    # 清理未使用的卷
    echo "🗑️  清理未使用的卷..."
    docker volume prune -f
    
    # 再次检查空间
    AVAILABLE_SPACE=$(df / | awk 'NR==2 {print $4}')
    if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
        echo "❌ 清理后空间仍不足，可用空间: $(($AVAILABLE_SPACE / 1024 / 1024))MB"
        echo "❌ 需要至少 5GB 可用空间"
        exit 1
    else
        echo "✅ 清理完成，可用空间: $(($AVAILABLE_SPACE / 1024 / 1024))MB"
    fi
else
    echo "✅ 磁盘空间充足，可用空间: $(($AVAILABLE_SPACE / 1024 / 1024))MB"
fi

# 登录到阿里云容器镜像服务
# docker login --username=<你的阿里云用户名> crpi-rm17rxbil8uscdf1.cn-shenzhen.personal.cr.aliyuncs.com

# 拉取指定版本的镜像
echo "📦 拉取Docker镜像..."
docker pull crpi-rm17rxbil8uscdf1.cn-shenzhen.personal.cr.aliyuncs.com/xposl/home:${IMAGE_VERSION}

# 检查镜像拉取是否成功
if [ $? -ne 0 ]; then
    echo "❌ 镜像拉取失败，请检查网络连接和镜像版本"
    exit 1
fi

# 使用docker-compose部署
echo "🔄 重新部署容器..."
TAG=${IMAGE_VERSION} docker compose -f docker-compose.prod.yml down
TAG=${IMAGE_VERSION} docker compose -f docker-compose.prod.yml up -d

# 等待容器启动
echo "⏳ 等待容器启动..."
sleep 10

# 检查容器是否运行
if docker ps | grep -q "investnote"; then
    echo "✅ 容器启动成功"
else
    echo "❌ 容器启动失败"
    exit 1
fi

# 安装/更新 crontab 定时任务
echo "⏰ 更新crontab定时任务..."
if [ -f "scripts/crontab" ]; then
    # 备份当前crontab
    crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
    
    # 删除旧的InvestNote相关任务
    crontab -l 2>/dev/null | grep -v "investnote" | crontab - 2>/dev/null || true
    
    # 安装新的crontab
    crontab scripts/crontab
    
    echo "✅ Crontab已更新"
    echo "📋 当前定时任务:"
    crontab -l | grep -E "(ticker|news|investnote)" || echo "  未找到相关任务"
else
    echo "⚠️  警告: scripts/crontab文件不存在，跳过crontab更新"
fi

# 显示运行状态
echo "📊 部署状态检查:"
echo "  - Docker容器: $(docker ps --format 'table {{.Names}}\t{{.Status}}' | grep investnote || echo '❌ 未运行')"
echo "  - API健康检查: $(curl -s http://localhost:8000/health | jq -r .status 2>/dev/null || echo '❌ 检查失败')"

# 部署完成后的清理建议
echo "🧹 部署完成后的清理建议:"
echo "  - 运行 'docker system df' 查看Docker资源使用情况"
echo "  - 运行 'docker system prune -a' 清理未使用的资源（谨慎使用）"
echo "  - 定期清理日志文件: 'find /var/log -name '*.log' -mtime +7 -delete'"

echo "🎉 部署完成！版本: ${IMAGE_VERSION}"
echo "🔗 访问地址: http://localhost:8000"