# ============================================================================
# 企业知识库 RAG 问答系统 - 知识盲区模型
# 功能：统计未在知识库中找到答案的问题，帮助管理员发现知识缺口
# ============================================================================

from utils import db
from datetime import datetime


class KnowledgeGap(db.Model):
    """知识盲区记录 - 统计未命中的用户问题"""
    __tablename__ = 'knowledge_gaps'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='记录ID')
    question = db.Column(db.String(500), nullable=False, comment='用户问题')
    question_hash = db.Column(db.String(32), nullable=False, comment='问题MD5（用于去重统计）')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), comment='提问用户')
    category = db.Column(db.String(100), comment='问题分类（自动归类）')
    hit_count = db.Column(db.Integer, default=1, comment='出现次数')
    first_asked = db.Column(db.DateTime, default=datetime.now, comment='首次提问')
    last_asked = db.Column(db.DateTime, default=datetime.now, comment='最近提问')

    user = db.relationship('User', backref='knowledge_gaps', lazy='joined')

    __table_args__ = (
        db.Index('idx_question_hash', 'question_hash'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'question': self.question,
            'category': self.category,
            'hit_count': self.hit_count,
            'first_asked': self.first_asked.isoformat() if self.first_asked else None,
            'last_asked': self.last_asked.isoformat() if self.last_asked else None,
        }
