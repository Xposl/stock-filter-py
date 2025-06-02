#!/bin/bash

# 设置变量
IMAGE_VERSION=$1
if [ -z "$IMAGE_VERSION" ]; then
  echo "请提供镜像版本号"
  echo "用法: ./deploy.sh <版本号>"
  exit 1
fi

echo "🚀 开始部署InvestNote-py版本: ${IMAGE_VERSION}"

# 登录到阿里云容器镜像服务
# docker login --username=<你的阿里云用户名> crpi-rm17rxbil8uscdf1.cn-shenzhen.personal.cr.aliyuncs.com

# 拉取指定版本的镜像
echo "📦 拉取Docker镜像..."
docker pull crpi-rm17rxbil8uscdf1.cn-shenzhen.personal.cr.aliyuncs.com/xposl/home:${IMAGE_VERSION}

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

echo "🎉 部署完成！版本: ${IMAGE_VERSION}"
echo "🔗 访问地址: http://localhost:8000"