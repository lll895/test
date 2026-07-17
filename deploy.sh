# ============================================================================
# 企业知识库 RAG 问答系统 - 一键部署脚本（Ubuntu 22.04+）
# ============================================================================
# 使用方法：
#   1. 将项目上传到服务器
#   2. chmod +x deploy.sh
#   3. sudo ./deploy.sh
# ============================================================================

set -e

PROJECT_DIR=$(pwd)
DOMAIN="${DOMAIN:-your-domain.com}"  # 修改为你的域名或服务器 IP

echo "=========================================="
echo "  企业知识库部署脚本"
echo "  目标: $DOMAIN"
echo "=========================================="

# ---------- 后端部署 ----------
echo ""
echo "📦 部署后端..."

cd "$PROJECT_DIR/server"

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt gunicorn pymysql cryptography

# 创建 .env 配置文件
cat > .env << EOF
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=dbenterprise
OLLAMA_BASE_URL=http://127.0.0.1:11434
LLM_MODEL=qwen2.5:3b
EMBEDDING_MODEL=qwen3-embedding:4b
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
LOG_LEVEL=INFO
FLASK_ENV=production
EOF

# 初始化数据库
python -c "from scripts.migrate import run; run()"
python -c "from scripts.seed_workflow import run; run()"

# 配置 systemd 服务
sudo tee /etc/systemd/system/enterprise-oa.service > /dev/null << EOF
[Unit]
Description=Enterprise OA Backend
After=network.target mysql.service redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=$PROJECT_DIR/server
EnvironmentFile=$PROJECT_DIR/server/.env
ExecStart=$PROJECT_DIR/server/.venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable enterprise-oa
sudo systemctl start enterprise-oa

echo "✅ 后端已启动!"

# ---------- 前端部署 ----------
echo ""
echo "📦 部署前端..."

cd "$PROJECT_DIR/client"
npm install
npx vite build

# 配置 Nginx
sudo tee /etc/nginx/sites-available/enterprise-oa > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN;

    # 前端静态文件
    root $PROJECT_DIR/client/dist;
    index index.html;

    # Gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript image/svg+xml;

    # API 反向代理到 Flask
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # SSE 支持（流式问答）
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }

    # SPA 路由（所有路径返回 index.html）
    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/enterprise-oa /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

echo "✅ Nginx 配置完成!"

echo ""
echo "=========================================="
echo "  🎉 部署完成！"
echo ""
echo "  访问地址: http://$DOMAIN"
echo "  后端 API: http://$DOMAIN/api"
echo "  健康检查: http://$DOMAIN/api/health"
echo ""
echo "  需要配置 HTTPS 请运行:"
echo "  sudo apt install -y certbot python3-certbot-nginx"
echo "  sudo certbot --nginx -d $DOMAIN"
echo "=========================================="
