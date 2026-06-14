# JobMatch AI Backend - CloudBase Run Dockerfile (Root)
FROM python:3.11-slim

WORKDIR /app

# 安装基础系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 复制后端依赖并安装
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制整个项目（包含 backend/ 和 data/）
COPY . .

# 创建必要目录
RUN mkdir -p /app/uploads

EXPOSE 8000

# 使用 server.py 启动（纯标准库，稳定）
CMD ["python", "server.py"]
