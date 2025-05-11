FROM python:3.13-slim AS builder

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.7.1

# 配置pip使用清华源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 安装系统依赖
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 生产环境镜像
FROM python:3.13-slim

WORKDIR /app

# 安装 Pyppeteer 和 Chromium 依赖 - 添加了字体和国际化支持
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    libxss1 \
    libxtst6 \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libglib2.0-0 \
    curl \
    fonts-noto-cjk \
    locales \
    && rm -rf /var/lib/apt/lists/* \
    && locale-gen zh_CN.UTF-8

# 配置中文支持
ENV LANG=zh_CN.UTF-8 \
    LANGUAGE=zh_CN:zh \
    LC_ALL=zh_CN.UTF-8

# 配置pip使用清华源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 设置 Pyppeteer 环境变量 - 添加了Docker容器特定参数
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=false \
    PYPPETEER_HOME=/app/.pyppeteer \
    PUPPETEER_DOWNLOAD_HOST=https://npmmirror.com/mirrors/ \
    PYPPETEER_CHROMIUM_REVISION=1181205

# 创建持久化目录并设置权限
RUN mkdir -p /app/.pyppeteer && chmod -R 777 /app/.pyppeteer

# 直接在最终镜像中安装所有Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建自定义的Pyppeteer初始化脚本
RUN echo '#!/usr/bin/env python3\n\
import os\n\
import asyncio\n\
from pyppeteer import launch\n\
import pyppeteer.chromium_downloader as downloader\n\
\n\
async def docker_init():\n\
    print("正在Docker环境中初始化Pyppeteer...")\n\
    try:\n\
        browser_args = [\n\
            "--no-sandbox",\n\
            "--disable-setuid-sandbox",\n\
            "--disable-dev-shm-usage",\n\
            "--disable-gpu",\n\
            "--no-zygote",\n\
            "--single-process"\n\
        ]\n\
        browser = await launch(headless=True, args=browser_args)\n\
        version = await browser.version()\n\
        print(f"成功启动浏览器: {version}")\n\
        await browser.close()\n\
        print("浏览器正常关闭，初始化成功")\n\
        return True\n\
    except Exception as e:\n\
        print(f"初始化出错: {e}")\n\
        return False\n\
\n\
loop = asyncio.get_event_loop()\n\
success = loop.run_until_complete(docker_init())\n\
if not success:\n\
    print("初始化失败，但将继续构建")\n\
' > /app/docker_init_pyppeteer.py && chmod +x /app/docker_init_pyppeteer.py

# 直接下载Chromium而不是通过pyppeteer下载
RUN mkdir -p /app/.pyppeteer/local-chromium/1181205 \
    && apt-get update && apt-get install -y wget unzip \
    && cd /app/.pyppeteer/local-chromium/1181205 \
    && echo "下载Chromium..." \
    && wget -q https://npmmirror.com/mirrors/chromium-browser-snapshots/Linux_x64/1181205/chrome-linux.zip \
    && echo "解压Chromium..." \
    && unzip -q chrome-linux.zip \
    && rm chrome-linux.zip \
    && chmod +x chrome-linux/chrome \
    && apt-get remove -y wget unzip \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* \
    && python /app/docker_init_pyppeteer.py || true

# 创建非root用户
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app

USER appuser

# 确保 Python 可执行文件目录在PATH中
ENV PATH="/usr/local/bin:${PATH}"

# 验证uvicorn是否可用
RUN which uvicorn || echo "uvicorn not found in PATH"

# 暴露端口
EXPOSE 8000

# 修改启动命令，使用绝对路径
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
