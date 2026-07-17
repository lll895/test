# ============================================================================
# 企业知识库 RAG 问答系统 - 文档处理服务
# 功能：处理上传的文档文件，提取文本内容，进行向量化存储
# ============================================================================

from models.document import Document, DocumentChunk
from services.vector_service import vector_service
from utils import db
from utils.logger import get_logger
import os

logger = get_logger(__name__)


class DocumentService:
    """
    文档处理服务类
    负责文档上传后的文本提取、切分、向量化全流程
    """

    # 支持的文件类型
    SUPPORTED_EXTENSIONS = {
        '.txt': 'txt',
        '.md': 'md',
        '.pdf': 'pdf',
        '.docx': 'docx',
    }

    UPLOAD_DIR = './uploads'  # 文件上传存储目录

    def __init__(self):
        """初始化文档服务，确保上传目录存在"""
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)

    @staticmethod
    def extract_text(file_path: str, file_type: str) -> str:
        """
        根据文件类型提取文本内容

        Args:
            file_path: 文件路径
            file_type: 文件类型（txt/md/pdf/docx）

        Returns:
            提取的文本内容
        """
        text = ""
        try:
            if file_type in ('txt', 'md'):
                # 文本文件直接读取
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()

            elif file_type == 'pdf':
                # PDF 文件使用 PyPDF2 提取
                from PyPDF2 import PdfReader
                reader = PdfReader(file_path)
                for page in reader.pages:
                    text += page.extract_text() + "\n"

            elif file_type == 'docx':
                # Word 文件使用 python-docx 提取
                from docx import Document as DocxDocument
                doc = DocxDocument(file_path)
                for para in doc.paragraphs:
                    text += para.text + "\n"

            logger.info(f"文本提取完成: {len(text)} 字符")
        except Exception as e:
            logger.error(f"文本提取失败: {e}")
            raise

        return text

    def process_document(self, doc_id: int, title: str, content: str) -> bool:
        """
        处理文档：切分文本 → 向量化存储 → 更新数据库记录

        Args:
            doc_id: 文档ID
            title: 文档标题
            content: 文档文本内容

        Returns:
            处理是否成功
        """
        try:
            logger.info(f"开始处理文档 ID={doc_id}: {title}")

            # 1. 将文档添加到向量数据库
            chunks = vector_service.add_document(doc_id, title, content)

            # 2. 将文本块信息保存到数据库
            for chunk_data in chunks:
                doc_chunk = DocumentChunk(
                    document_id=doc_id,
                    chunk_index=chunk_data['chunk_index'],
                    content=chunk_data['content'],
                    vector_id=chunk_data.get('vector_id', ''),
                    token_count=len(chunk_data['content']),
                )
                db.session.add(doc_chunk)

            # 3. 更新文档状态
            doc = Document.query.get(doc_id)
            if doc:
                doc.status = 'ready'
                doc.chunk_count = len(chunks)
                doc.content_text = content[:50000]  # 只保存前50000字符
                # 自动生成摘要（取前200字符）
                doc.summary = content[:200] + '...' if len(content) > 200 else content

            db.session.commit()
            logger.info(f"文档 '{title}' 处理完成，共 {len(chunks)} 个文本块")
            return True

        except Exception as e:
            db.session.rollback()
            logger.error(f"文档 '{title}' 处理失败: {e}")

            # 更新文档状态为失败
            doc = Document.query.get(doc_id)
            if doc:
                doc.status = 'failed'
                doc.error_message = str(e)
                db.session.commit()
            return False


# 全局单例
document_service = DocumentService()
