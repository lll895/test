"""
企业知识库 RAG 问答系统 - 自定义异常与错误监控
=============================================
功能：
- 统一的自定义异常类
- 标准化的错误响应格式
- Sentry 集成（可选）
"""

import os
import traceback
from flask import jsonify
from utils.logger import get_logger

logger = get_logger(__name__)


# ==================== 自定义异常类 ====================

class AppError(Exception):
    """应用基础异常"""

    def __init__(self, message: str, code: int = 500, data=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.data = data

    def to_response(self):
        """转换为 Flask JSON 响应"""
        return jsonify({
            'code': self.code,
            'data': self.data,
            'message': self.message,
        }), self.code


class NotFoundError(AppError):
    """资源未找到异常（404）"""

    def __init__(self, message: str = '请求的资源不存在', data=None):
        super().__init__(message, code=404, data=data)


class AuthError(AppError):
    """认证授权异常（401/403）"""

    def __init__(self, message: str = '未授权访问', code: int = 401, data=None):
        super().__init__(message, code=code, data=data)


class ValidationError(AppError):
    """参数校验异常（400）"""

    def __init__(self, message: str = '请求参数无效', field: str = None, data=None):
        if field:
            message = f"字段 '{field}' 校验失败: {message}"
        super().__init__(message, code=400, data=data)


class ServiceError(AppError):
    """服务层异常（500）"""

    def __init__(self, message: str = '服务处理失败', data=None, cause: Exception = None):
        super().__init__(message, code=500, data=data)
        self.cause = cause


class ConfigError(AppError):
    """配置异常（启动时验证用）"""

    def __init__(self, message: str = '配置错误'):
        super().__init__(message, code=500)


# ==================== Sentry 集成 ====================

_sentry_initialized = False


def init_sentry(app):
    """
    初始化 Sentry 错误监控（通过 SENTRY_DSN 环境变量控制）
    如需启用，设置环境变量：SENTRY_DSN=https://xxx@sentry.io/xxx

    Args:
        app: Flask 应用实例
    """
    global _sentry_initialized

    dsn = os.environ.get('SENTRY_DSN', '').strip()
    if not dsn:
        logger.info("Sentry 未配置（跳过）")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=dsn,
            integrations=[
                FlaskIntegration(),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=float(os.environ.get('SENTRY_TRACES_SAMPLE_RATE', '0.1')),
            environment=os.environ.get('FLASK_ENV', 'development'),
        )
        _sentry_initialized = True
        logger.info(f"Sentry 错误监控已初始化 (DSN: {dsn[:20]}...)")
    except ImportError:
        logger.warning("sentry-sdk 未安装，Sentry 集成跳过（如需使用：pip install sentry-sdk）")
    except Exception as e:
        logger.error(f"Sentry 初始化失败: {e}")


def is_sentry_active() -> bool:
    """检查 Sentry 是否已启用"""
    return _sentry_initialized


# ==================== 全局错误处理注册函数 ====================

def register_error_handlers(app):
    """
    在 Flask 应用中注册全局错误处理器

    Args:
        app: Flask 应用实例
    """

    @app.errorhandler(AppError)
    def handle_app_error(error):
        """处理自定义应用异常"""
        if error.code >= 500:
            logger.error(f"应用异常: {error.message}", exc_info=True)
        else:
            logger.warning(f"应用异常: {error.code} - {error.message}")
        return error.to_response()

    @app.errorhandler(404)
    def handle_404(error):
        """处理 404 错误"""
        logger.warning(f"404 未找到: {error}")
        return jsonify({'code': 404, 'data': None, 'message': '请求的资源不存在'}), 404

    @app.errorhandler(405)
    def handle_405(error):
        """处理 405 方法不允许"""
        logger.warning(f"405 方法不允许: {error}")
        return jsonify({'code': 405, 'data': None, 'message': '请求方法不允许'}), 405

    @app.errorhandler(500)
    def handle_500(error):
        """处理 500 内部错误"""
        logger.error(f"服务器内部错误: {error}", exc_info=True)
        return jsonify({'code': 500, 'data': None, 'message': '服务器内部错误，请稍后再试'}), 500

    @app.errorhandler(Exception)
    def handle_unhandled(error):
        """处理所有未捕获的异常"""
        logger.critical(f"未捕获的异常: {error}\n{traceback.format_exc()}")
        return jsonify({'code': 500, 'data': None, 'message': '服务器内部错误，请稍后再试'}), 500

    logger.info("全局错误处理器已注册")
