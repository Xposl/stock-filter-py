FROM python:3.13-slim as builder

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

# 安装 Pyppeteer 和 Chromium 依赖
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
    && rm -rf /var/lib/apt/lists/*

# 配置pip使用清华源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 设置 Pyppeteer 环境变量
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=false \
    PYPPETEER_HOME=/app/.pyppeteer \
    PUPPETEER_DOWNLOAD_HOST=https://npmmirror.com/mirrors/

# 复制依赖
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/

# 复制应用代码
COPY . .

# 运行初始化脚本下载 Chromium
RUN python tools/init_pyppeteer.py

# 创建非root用户
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app

USER appuser

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
