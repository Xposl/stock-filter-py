#!/bin/bash

# 快速Docker构建脚本
# 使用多阶段构建和缓存优化

echo "🚀 开始优化的Docker构建..."

# 清理旧的构建缓存
echo "🧹 清理Docker构建缓存..."
docker builder prune -f

# 启用BuildKit以获得更好的性能
export DOCKER_BUILDKIT=1

# 构建镜像，使用缓存
echo "🏗️ 构建Docker镜像（使用缓存优化）..."
docker compose build --parallel

# 启动服务
echo "🎯 启动InvestNote服务..."
docker compose up -d

echo "✅ 构建完成！"
echo "📊 查看日志: docker compose logs -f"
echo "🔗 访问应用: http://localhost:8000"
