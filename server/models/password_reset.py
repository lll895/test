"""
企业知识库 RAG 问答系统 - 密码重置令牌模型
=========================================
独立的令牌表，避免在 User 模型上添加字段导致数据库迁移问题。
"""

from utils import db
from datetime import datetime
from config import Config


class PasswordResetToken(db.Model):
    """密码重置令牌 - 独立表结构，无需修改 users 表"""
    __tablename__ = 'password_reset_tokens'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='ID')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                        nullable=False, comment='用户ID')
    token = db.Column(db.String(64), unique=True, nullable=False, index=True, comment='重置令牌')
    expires_at = db.Column(db.DateTime, nullable=False, comment='过期时间')
    used = db.Column(db.Boolean, default=False, comment='是否已使用')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    user = db.relationship('User', backref='reset_tokens', lazy='joined')

    @property
    def is_expired(self) -> bool:
        """令牌是否已过期"""
        return datetime.now() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """令牌是否有效（未使用且未过期）"""
        return not self.used and not self.is_expired

    @classmethod
    def create_for_user(cls, user_id: int, ttl_seconds: int = 1800) -> 'PasswordResetToken':
        """
        为用户创建重置令牌

        Args:
            user_id: 用户ID
            ttl_seconds: 令牌有效期（秒），默认30分钟

        Returns:
            创建的令牌实例
        """
        import uuid
        # 使该用户之前的令牌失效
        cls.query.filter_by(user_id=user_id, used=False).update({'used': True})

        token_str = uuid.uuid4().hex
        expires = datetime.now() + __import__('datetime').timedelta(seconds=ttl_seconds)

        reset_token = cls(
            user_id=user_id,
            token=token_str,
            expires_at=expires,
        )
        db.session.add(reset_token)
        db.session.commit()

        return reset_token

    @classmethod
    def verify_and_consume(cls, token: str) -> 'PasswordResetToken':
        """
        验证令牌并标记为已使用

        Args:
            token: 令牌字符串

        Returns:
            有效的令牌对象，如果无效返回 None
        """
        record = cls.query.filter_by(token=token, used=False).first()
        if not record or record.is_expired:
            return None

        record.used = True
        db.session.commit()
        return record
