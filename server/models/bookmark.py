# ============================================================================
# 企业知识库 RAG 问答系统 - 收藏夹模型
# 功能：用户收藏问答和文档，添加个人笔记
# ============================================================================

from utils import db
from datetime import datetime


class Bookmark(db.Model):
    """收藏记录模型 - 用户收藏的问答或文档"""
    __tablename__ = 'bookmarks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='收藏ID')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                        nullable=False, comment='用户ID')
    type = db.Column(db.Enum('qa', 'document'), nullable=False, comment='收藏类型：qa问答 / document文档')
    target_id = db.Column(db.Integer, nullable=False, comment='目标ID（问答ID或文档ID）')
    note = db.Column(db.Text, comment='个人笔记')
    tags = db.Column(db.String(500), comment='标签（逗号分隔）')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # 关联
    user = db.relationship('User', backref='bookmarks', lazy='joined')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'type', 'target_id', name='uq_user_bookmark'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'target_id': self.target_id,
            'note': self.note,
            'tags': self.tags.split(',') if self.tags else [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
