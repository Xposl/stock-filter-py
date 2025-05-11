#!/bin/bash

# 设置变量
IMAGE_VERSION=$1
if [ -z "$IMAGE_VERSION" ]; then
  echo "请提供镜像版本号"
  echo "用法: ./deploy.sh <版本号>"
  exit 1
fi

# 登录到阿里云容器镜像服务
# docker login --username=<你的阿里云用户名> crpi-rm17rxbil8uscdf1.cn-shenzhen.personal.cr.aliyuncs.com

# 拉取指定版本的镜像
docker pull crpi-rm17rxbil8uscdf1.cn-shenzhen.personal.cr.aliyuncs.com/xposl/home:${IMAGE_VERSION}

# 使用docker-compose部署
TAG=${IMAGE_VERSION} docker compose -f docker-compose.prod.yml down
TAG=${IMAGE_VERSION} docker compose -f docker-compose.prod.yml up -d

echo "部署完成！版本: ${IMAGE_VERSION}"