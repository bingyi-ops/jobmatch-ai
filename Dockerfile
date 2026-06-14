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

# 创建必要目录（server.py 在 backend/ 下运行时，uploads 也在 backend/）
RUN mkdir -p /app/backend/uploads

EXPOSE 8000

# 关键修复：WORKDIR 必须在 backend/ 下，因为：
#   1. server.py 中的 from app.llm 需要能在当前目录找到 app/ 包
#   2. schema 路径通过 .. 向上找到 data/schema.sql
WORKDIR /app/backend

# 使用 server.py 启动（纯标准库，稳定）
CMD ["python", "server.py"]
