"""
企业知识库 RAG 问答系统 - 健康检查端点
=====================================
功能：
- /api/health      → 综合健康检查（数据库、Redis、向量库、LLM）
- /api/health/ready → 就绪检查（K8s  readiness probe）
- /api/health/live  → 存活检查（K8s  liveness probe）
"""

from flask import Blueprint, jsonify
from utils import db
from utils.logger import get_logger

logger = get_logger(__name__)

# 创建健康检查蓝图
health_bp = Blueprint('health', __name__, url_prefix='/api/health')

# ---------- 全局状态缓存 ----------
_health_cache = {}
_health_cache_ttl = 30  # 秒


def _check_database() -> dict:
    """检查数据库连接状态"""
    try:
        db.session.execute(db.text('SELECT 1'))
        return {'status': 'ok', 'message': '数据库连接正常'}
    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        return {'status': 'error', 'message': f'数据库连接失败: {str(e)}'}


def _check_redis() -> dict:
    """检查 Redis 连接状态"""
    try:
        from services.cache_service import cache_service
        if cache_service.is_connected:
            return {'status': 'ok', 'message': 'Redis 连接正常'}
        return {'status': 'degraded', 'message': 'Redis 未连接，缓存降级为直读模式'}
    except Exception as e:
        return {'status': 'error', 'message': f'Redis 检查失败: {str(e)}'}


def _check_vector_store() -> dict:
    """检查向量数据库（Chroma）连接状态"""
    try:
        from services.vector_service import vector_service
        # 尝试获取文档计数来验证连接
        count = vector_service.get_document_count()
        return {'status': 'ok', 'message': f'向量库连接正常, 文档数: {count}'}
    except Exception as e:
        return {'status': 'error', 'message': f'向量库连接失败: {str(e)}'}


def _check_llm() -> dict:
    """检查大语言模型服务（Ollama）连接状态"""
    try:
        from services.llm_service import llm_service
        if llm_service._llm is not None:
            return {'status': 'ok', 'message': f'LLM 已初始化 ({llm_service.model_name})'}
        return {'status': 'ok', 'message': f'LLM 配置正常 ({llm_service.model_name})，延迟初始化'}
    except Exception as e:
        return {'status': 'error', 'message': f'LLM 检查失败: {str(e)}'}


@health_bp.route('', methods=['GET'])
def health_check():
    """
    综合健康检查
    检查所有依赖服务的连接状态
    """
    db_status = _check_database()
    redis_status = _check_redis()
    vector_status = _check_vector_store()
    llm_status = _check_llm()

    # 计算总体状态
    all_checks = [db_status, redis_status, vector_status, llm_status]
    errors = [c for c in all_checks if c['status'] == 'error']
    degraded = [c for c in all_checks if c['status'] == 'degraded']

    if errors:
        overall = 'degraded' if len(errors) < len(all_checks) else 'error'
    else:
        overall = 'ok'

    return jsonify({
        'status': overall,
        'timestamp': __import__('datetime').datetime.now().isoformat(),
        'checks': {
            'database': db_status,
            'redis': redis_status,
            'vector_store': vector_status,
            'llm': llm_status,
        },
        'summary': {
            'total': len(all_checks),
            'ok': sum(1 for c in all_checks if c['status'] == 'ok'),
            'degraded': len(degraded),
            'error': len(errors),
        }
    })


@health_bp.route('/live', methods=['GET'])
def liveness_probe():
    """
    存活检查（Liveness Probe）
    用于 K8s / Docker 判断进程是否存活
    """
    return jsonify({
        'status': 'ok',
        'timestamp': __import__('datetime').datetime.now().isoformat(),
    })


@health_bp.route('/ready', methods=['GET'])
def readiness_probe():
    """
    就绪检查（Readiness Probe）
    用于 K8s / Docker 判断服务是否可接收流量
    """
    db_status = _check_database()

    overall = 'ok' if db_status['status'] == 'ok' else 'error'
    http_code = 200 if overall == 'ok' else 503

    return jsonify({
        'status': overall,
        'timestamp': __import__('datetime').datetime.now().isoformat(),
        'checks': {
            'database': db_status,
        }
    }), http_code
