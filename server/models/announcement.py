# ============================================================================
# 企业知识库 RAG 问答系统 - 公告模型
# ============================================================================

from utils import db
from datetime import datetime


class Announcement(db.Model):
    """系统公告模型 - 管理员发布系统公告"""
    __tablename__ = 'announcements'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='公告ID')
    title = db.Column(db.String(255), nullable=False, comment='公告标题')
    content = db.Column(db.Text, nullable=False, comment='公告内容')
    priority = db.Column(db.Enum('low', 'normal', 'high'), default='normal', comment='优先级')
    published_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                             nullable=False, comment='发布者ID')
    is_active = db.Column(db.Boolean, default=True, comment='是否生效')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # 关联关系
    publisher = db.relationship('User', backref='announcements', lazy='joined')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'priority': self.priority,
            'publisher': self.publisher.real_name or self.publisher.username if self.publisher else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
