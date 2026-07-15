# ============================================================================
# 企业知识库 RAG 问答系统 - 数据库初始化模块
# ============================================================================

from flask_sqlalchemy import SQLAlchemy
from flask import Flask

# 创建全局 SQLAlchemy 实例
db = SQLAlchemy()


def init_db(app: Flask):
    """
    初始化数据库连接
    Args:
        app: Flask 应用实例
    """
    db.init_app(app)
    with app.app_context():
        # 创建所有数据表（如果尚不存在）
        db.create_all()
        print("[数据库] 数据表初始化完成")
