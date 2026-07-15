# ============================================================================
# 企业知识库 RAG 问答系统 - 文档模型
# ============================================================================

from utils import db
from datetime import datetime


class Category(db.Model):
    """文档分类模型 - 对知识库文档进行分类管理"""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='分类ID')
    name = db.Column(db.String(100), nullable=False, comment='分类名称')
    description = db.Column(db.String(500), comment='分类描述')
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), comment='父分类ID')
    sort_order = db.Column(db.Integer, default=0, comment='排序序号')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # 关联关系
    children = db.relationship('Category', backref=db.backref('parent', remote_side=[id]),
                               lazy='dynamic')
    documents = db.relationship('Document', backref='category', lazy='dynamic')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'parent_id': self.parent_id,
            'sort_order': self.sort_order,
            'doc_count': self.documents.filter(Document.status == 'ready').count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Document(db.Model):
    """文档模型 - 存储上传的知识文档元信息"""
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='文档ID')
    title = db.Column(db.String(255), nullable=False, comment='文档标题')
    file_name = db.Column(db.String(255), nullable=False, comment='原始文件名')
    file_path = db.Column(db.String(500), comment='文件存储路径')
    file_size = db.Column(db.BigInteger, default=0, comment='文件大小（字节）')
    file_type = db.Column(db.String(50), comment='文件类型')
    content_text = db.Column(db.Text, comment='提取的文本内容')
    summary = db.Column(db.Text, comment='文档摘要')
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), comment='所属分类')
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='上传者')
    status = db.Column(db.Enum('processing', 'ready', 'failed'), default='processing', comment='处理状态')
    chunk_count = db.Column(db.Integer, default=0, comment='文本块数量')
    error_message = db.Column(db.Text, comment='错误信息')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # 关联关系
    chunks = db.relationship('DocumentChunk', backref='document', lazy='dynamic',
                             cascade='all, delete-orphan')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'summary': self.summary,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'uploader': self.uploader.real_name or self.uploader.username if self.uploader else None,
            'status': self.status,
            'chunk_count': self.chunk_count,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class DocumentChunk(db.Model):
    """文档块模型 - 存储文档切分后的文本块"""
    __tablename__ = 'document_chunks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='块ID')
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id', ondelete='CASCADE'),
                            nullable=False, comment='所属文档ID')
    chunk_index = db.Column(db.Integer, nullable=False, comment='块序号')
    content = db.Column(db.Text, nullable=False, comment='文本块内容')
    token_count = db.Column(db.Integer, default=0, comment='Token数量估算')
    vector_id = db.Column(db.String(100), comment='Chroma向量ID')
    created_at = db.Column(db.DateTime, default=datetime.now, comment='创建时间')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'chunk_index': self.chunk_index,
            'content': self.content[:200] + '...' if len(self.content) > 200 else self.content,
            'token_count': self.token_count,
            'vector_id': self.vector_id,
        }
