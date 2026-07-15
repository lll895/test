# ============================================================================
# 企业知识库 RAG 问答系统 - 跨设备对话同步模型
# 功能：持久化保存用户对话历史，支持多设备同步
# ============================================================================

from utils import db
from datetime import datetime
from sqlalchemy.dialects.mysql import JSON
import json


class Conversation(db.Model):
    """对话会话模型 - 保存用户的完整对话"""
    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='会话ID')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                        nullable=False, comment='用户ID')
    session_id = db.Column(db.String(64), unique=True, nullable=False, comment='会话标识')
    title = db.Column(db.String(200), comment='会话标题（自动生成）')
    message_count = db.Column(db.Integer, default=0, comment='消息数')
    is_active = db.Column(db.Boolean, default=True, comment='是否激活')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    user = db.relationship('User', backref='conversations', lazy='joined')
    messages = db.relationship('ConversationMessage', backref='conversation',
                                lazy='dynamic', cascade='all, delete-orphan',
                                order_by='ConversationMessage.created_at')

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'title': self.title or '新对话',
            'message_count': self.message_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ConversationMessage(db.Model):
    """对话消息模型 - 存储单条对话消息"""
    __tablename__ = 'conversation_messages'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='消息ID')
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id', ondelete='CASCADE'),
                                nullable=False, comment='所属会话ID')
    role = db.Column(db.Enum('user', 'assistant'), nullable=False, comment='角色')
    content = db.Column(db.Text, nullable=False, comment='消息内容')
    sources = db.Column(JSON, comment='引用来源')
    cost_time_ms = db.Column(db.Integer, default=0, comment='耗时')
    chunks_retrieved = db.Column(db.Integer, default=0, comment='检索块数')
    feedback = db.Column(db.Integer, default=-1, comment='反馈')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    def to_dict(self):
        return {
            'id': self.id,
            'role': self.role,
            'content': self.content,
            'sources': json.loads(self.sources) if isinstance(self.sources, str) else self.sources,
            'cost_time_ms': self.cost_time_ms,
            'chunks_retrieved': self.chunks_retrieved,
            'feedback': self.feedback,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
