# JobMatch AI Backend - CloudBase Run Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装基础系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 复制并安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY . .

# 创建数据目录
RUN mkdir -p /app/data /app/uploads

EXPOSE 8000

# 使用 server.py 作为启动入口（纯标准库，不依赖缺失的 FastAPI 模块）
CMD ["python", "server.py"]
