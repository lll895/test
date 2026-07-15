# ============================================================================
# 企业知识库 RAG 问答系统 - 用户模型
# ============================================================================

from utils import db
from datetime import datetime


class User(db.Model):
    """用户模型 - 存储管理员和普通用户信息"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='用户ID')
    username = db.Column(db.String(50), unique=True, nullable=False, comment='用户名')
    password = db.Column(db.String(64), nullable=False, comment='密码（MD5加密）')
    real_name = db.Column(db.String(50), comment='真实姓名')
    email = db.Column(db.String(100), comment='邮箱')
    role = db.Column(db.Enum('admin', 'user'), nullable=False, default='user', comment='角色')
    status = db.Column(db.Boolean, nullable=False, default=True, comment='状态：1启用 0禁用')
    avatar = db.Column(db.String(255), comment='头像URL')
    last_login = db.Column(db.DateTime, comment='最后登录时间')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # 关联关系
    documents = db.relationship('Document', backref='uploader', lazy='dynamic',
                                foreign_keys='Document.uploaded_by')

    def to_dict(self):
        """转换为字典（脱敏，不返回密码）"""
        return {
            'id': self.id,
            'username': self.username,
            'real_name': self.real_name,
            'email': self.email,
            'role': self.role,
            'status': self.status,
            'avatar': self.avatar,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def has_permission(self, required_role: str) -> bool:
        """
        检查用户是否有指定角色的权限
        Args:
            required_role: 需要的角色名 ('admin' 或 'user')
        Returns:
            是否有权限
        """
        if required_role == 'admin':
            return self.role == 'admin'
        return True  # 所有登录用户都有 user 权限
