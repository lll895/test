# ============================================================================
# 企业知识库 RAG 问答系统 - Flask 应用入口
# 功能：创建 Flask 应用实例，注册所有蓝图和中间件
# ============================================================================

import os
import sys

# 将项目目录加入 Python 路径，确保模块可以正确导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from utils import init_db
from services.cache_service import cache_service

# ---------- 先导入所有模型，确保 db.create_all() 能创建所有表 ----------
from models.user import User
from models.document import Document, Category, DocumentChunk
from models.qa_log import QaLog
from models.announcement import Announcement
from models.bookmark import Bookmark
from models.conversation import Conversation, ConversationMessage
from models.workflow import WorkflowAction
from models.knowledge_gap import KnowledgeGap

# ---------- 创建 Flask 应用 ----------
app = Flask(__name__)
app.config.from_object(Config)

# ---------- 配置 CORS（跨域请求支持） ----------
# 允许前端 localhost 域名访问后端 API
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
        "supports_credentials": True
    }
})

# ---------- 初始化 JWT 认证 ----------
jwt = JWTManager(app)


# JWT 错误处理
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    """Token 过期时的回调"""
    return jsonify({'code': 401, 'data': None, 'message': '登录已过期，请重新登录'}), 401


@jwt.invalid_token_loader
def invalid_token_callback(error):
    """无效 Token 时的回调"""
    return jsonify({'code': 401, 'data': None, 'message': '无效的认证令牌'}), 401


@jwt.unauthorized_loader
def missing_token_callback(error):
    """缺少 Token 时的回调"""
    return jsonify({'code': 401, 'data': None, 'message': '请先登录'}), 401


# ---------- 初始化数据库 ----------
init_db(app)

# ---------- 注册路由蓝图 ----------
from routes.auth import auth_bp
from routes.document import document_bp
from routes.qa import qa_bp
from routes.admin import admin_bp
from routes.bookmark import bookmark_bp
from routes.workflow import workflow_bp

app.register_blueprint(auth_bp)       # 认证：/api/auth/*
app.register_blueprint(document_bp)   # 文档：/api/documents/*
app.register_blueprint(qa_bp)         # 问答：/api/qa/*
app.register_blueprint(admin_bp)      # 管理：/api/admin/*
app.register_blueprint(bookmark_bp)   # 收藏：/api/bookmarks/*
app.register_blueprint(workflow_bp)   # 工作流：/api/workflow/*


# ---------- 根路由 ----------
@app.route('/')
def index():
    """服务根路径，返回服务状态信息"""
    return jsonify({
        'name': '企业知识库 RAG 问答系统 API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'auth': '/api/auth/*',
            'documents': '/api/documents/*',
            'qa': '/api/qa/*',
            'admin': '/api/admin/*',
        }
    })


# ---------- 全局错误处理 ----------
@app.errorhandler(404)
def not_found(error):
    """404 错误处理"""
    return jsonify({'code': 404, 'data': None, 'message': '请求的资源不存在'}), 404


@app.errorhandler(500)
def internal_error(error):
    """500 错误处理"""
    return jsonify({'code': 500, 'data': None, 'message': '服务器内部错误'}), 500


# ---------- 启动应用 ----------
if __name__ == '__main__':
    print("=" * 60)
    print("  企业知识库 RAG 问答系统")
    print(f"  服务启动: http://0.0.0.0:5000")
    print(f"  数据库: MySQL (dbenterprise)")
    print(f"  向量库: Chroma ({Config.CHROMA_PERSIST_DIR})")
    print(f"  缓存: Redis ({Config.REDIS_HOST}:{Config.REDIS_PORT})")
    print(f"  LLM: {Config.LLM_MODEL} ({Config.OLLAMA_BASE_URL})")
    print(f"  嵌入: {Config.EMBEDDING_MODEL}")
    print("=" * 60)

    # 缓存预热
    with app.app_context():
        try:
            from scripts.warm_cache import warm_cache
            warm_cache()
        except Exception as e:
            print(f"[启动] 缓存预热跳过: {e}")

    app.run(host='0.0.0.0', port=5000, debug=True)
