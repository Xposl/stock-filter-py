FROM python:3.13-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LANG=zh_CN.UTF-8 \
    LANGUAGE=zh_CN:zh \
    LC_ALL=zh_CN.UTF-8 \
    PYPPETEER_HOME=/app/.pyppeteer \
    PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=false \
    PUPPETEER_DOWNLOAD_HOST=https://npmmirror.com/mirrors/ \
    PYPPETEER_CHROMIUM_REVISION=1181205

# 配置apt源使用清华源加速下载
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources

# 合并系统依赖安装，减少镜像层数
RUN apt-get update && apt-get install -y --no-install-recommends \
    # 编译依赖
    gcc \
    g++ \
    git \
    curl \
    wget \
    unzip \
    build-essential \
    # PostgreSQL开发库
    libpq-dev \
    postgresql-client \
    # Python开发库
    python3-dev \
    # Chromium运行时依赖（只安装必要的）
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxss1 \
    xdg-utils \
    # 中文字体支持
    fonts-noto-cjk \
    locales \
    && locale-gen zh_CN.UTF-8 \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# 配置pip使用清华源并升级pip
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip install --upgrade pip

# 创建持久化目录并设置权限
RUN mkdir -p /app/.pyppeteer && chmod -R 777 /app/.pyppeteer

# 复制依赖文件并安装Python依赖
COPY requirements.txt .

# 安装剩余的核心依赖
RUN pip install --no-cache-dir -r requirements.txt || \
    (echo "部分依赖安装失败，继续使用已安装的依赖" && pip list)

# 预下载Chromium（在不复制代码的情况下）
RUN python -c "import asyncio; from pyppeteer import launch; asyncio.get_event_loop().run_until_complete(launch())" || echo "Chromium预下载完成或失败，将在运行时重试"

# 复制应用代码
COPY . .

# 创建非root用户
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app

USER appuser

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "main.py"]