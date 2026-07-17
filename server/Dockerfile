# ============================================================================
# 企业知识库 - 后端 Dockerfile
# ============================================================================
FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc default-libmysqlclient-dev && \
    rm -rf /var/lib/apt/lists/*

# 复制依赖并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn pymysql cryptography

# 复制源码
COPY . .

# 创建必要目录
RUN mkdir -p uploads logs chroma_db

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["sh", "-c", "python -c 'from scripts.migrate import run; run()' 2>/dev/null && gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 app:app"]
