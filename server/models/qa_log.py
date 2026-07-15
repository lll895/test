# ============================================================================
# 企业知识库 RAG 问答系统 - 问答日志模型
# ============================================================================

from utils import db
from datetime import datetime
from sqlalchemy.dialects.mysql import JSON
import json


class QaLog(db.Model):
    """问答记录模型 - 存储用户的提问和系统回答"""
    __tablename__ = 'qa_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='记录ID')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                        nullable=False, comment='提问用户')
    question = db.Column(db.Text, nullable=False, comment='用户问题')
    answer = db.Column(db.Text, comment='系统回答')
    sources = db.Column(JSON, comment='回答引用的来源文档信息')
    model_used = db.Column(db.String(100), comment='使用的模型')
    embedding_model = db.Column(db.String(100), comment='嵌入模型')
    chunks_retrieved = db.Column(db.Integer, default=0, comment='检索到的块数')
    tokens_used = db.Column(db.Integer, default=0, comment='消耗的Token数')
    cost_time_ms = db.Column(db.Integer, default=0, comment='耗时（毫秒）')
    feedback = db.Column(db.Integer, default=-1, comment='用户反馈：1有用 0无用 -1未评价')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    # 关联关系
    user = db.relationship('User', backref='qa_logs', lazy='joined')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.real_name or self.user.username if self.user else None,
            'question': self.question,
            'answer': self.answer,
            'sources': json.loads(self.sources) if isinstance(self.sources, str) else self.sources,
            'model_used': self.model_used,
            'chunks_retrieved': self.chunks_retrieved,
            'cost_time_ms': self.cost_time_ms,
            'feedback': self.feedback,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
