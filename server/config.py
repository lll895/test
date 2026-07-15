# ============================================================================
# 企业知识库 RAG 问答系统 - 配置文件
# ============================================================================

import os


class Config:
    """应用主配置类 - 包含所有环境通用的配置项"""

    # ---------- 密钥配置 ----------
    SECRET_KEY = os.environ.get('SECRET_KEY', 'enterprise-oa-secret-key-2024')

    # ---------- MySQL 数据库配置 ----------
    DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '17759400586')
    DB_NAME = os.environ.get('DB_NAME', 'dbenterprise')

    # SQLAlchemy 数据库连接 URI
    SQLALCHEMY_DATABASE_URI = (
        f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
        '?charset=utf8mb4'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---------- JWT 配置 ----------
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-enterprise-2024')
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # Token 过期时间：24小时（秒）

    # ---------- Ollama 配置 ----------
    OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://127.0.0.1:11434')
    LLM_MODEL = os.environ.get('LLM_MODEL', 'qwen2.5:3b')           # 大语言模型（3B快模型）
    LLM_MODEL_COMPLEX = os.environ.get('LLM_MODEL_COMPLEX', 'qwen3:8b')  # 复杂问题备用模型
    EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'qwen3-embedding:4b')  # 嵌入模型

    # ---------- Chroma 向量数据库配置 ----------
    CHROMA_PERSIST_DIR = os.environ.get('CHROMA_PERSIST_DIR', './chroma_db')
    CHROMA_COLLECTION_NAME = 'enterprise_knowledge'

    # ---------- RAG 配置 ----------
    # ---------- Redis 缓存配置 ----------
    REDIS_HOST = os.environ.get('REDIS_HOST', '127.0.0.1')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)
    REDIS_DECODE_RESPONSES = True

    # 缓存 TTL（秒）
    CACHE_TTL_QA = 3600           # 问答缓存：1小时
    CACHE_TTL_VECTOR = 1800       # 向量检索缓存：30分钟
    CACHE_TTL_DASHBOARD = 300     # 仪表盘缓存：5分钟
    CACHE_TTL_CATEGORIES = 600    # 分类缓存：10分钟
    CACHE_TTL_USER_STATS = 600    # 用户统计缓存：10分钟

    # Rate Limiting
    RATE_LIMIT_ENABLED = True
    RATE_LIMIT_DEFAULT = "100/minute"  # 默认：每分钟100次
    RATE_LIMIT_QA = "30/minute"        # 问答：每分钟30次

    CHUNK_SIZE = 500       # 文档切分的块大小（字符数）
    CHUNK_OVERLAP = 50     # 文档切分的块重叠（字符数）
    RETRIEVAL_K = 5        # 检索返回的最相关文档块数量
    RETRIEVAL_SCORE_THRESHOLD = 0.3  # 检索相似度阈值


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


# 配置映射表
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
