# JobMatch AI Backend - CloudBase Run Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装 Playwright 所需的系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk-bridge2.0-0 libdrm2 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libpango-1.0-0 libcairo2 libasound2 \
    libatspi2.0-0 libcups2 libx11-6 libxext6 libxrender1 \
    wget curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 复制并安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装 Playwright 浏览器（仅 Chromium）
RUN playwright install --with-deps chromium

# 复制后端代码
COPY . .

# 创建数据目录
RUN mkdir -p /app/data /app/uploads

EXPOSE 8000

CMD ["python", "-c", "import uvicorn; uvicorn.run('app.main:app', host='0.0.0.0', port=8000)"]
