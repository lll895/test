# ============================================================================
# 企业知识库 RAG 问答系统 - 工作流审批模型
# 功能：根据问答内容关键词匹配，自动显示审批/操作按钮
# ============================================================================

from utils import db
from datetime import datetime


class WorkflowAction(db.Model):
    """工作流动作模型 - 定义回答中显示的快捷操作按钮"""
    __tablename__ = 'workflow_actions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='动作ID')
    name = db.Column(db.String(100), nullable=False, comment='动作名称')
    keywords = db.Column(db.String(500), nullable=False, comment='触发关键词（逗号分隔，匹配到任意一个即显示）')
    label = db.Column(db.String(100), nullable=False, comment='按钮文字')
    url = db.Column(db.String(500), comment='跳转链接（支持占位符）')
    icon = db.Column(db.String(50), default='Link', comment='图标名')
    description = db.Column(db.String(200), comment='按钮描述')
    sort_order = db.Column(db.Integer, default=0, comment='排序')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'keywords': self.keywords.split(','),
            'label': self.label,
            'url': self.url,
            'icon': self.icon,
            'description': self.description,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
        }
