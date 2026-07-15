# ============================================================================
# 企业知识库 RAG 问答系统 - 文档重新索引脚本
# 功能：将 MySQL 中已标记为 ready 的文档重新向量化到 Chroma
# 用法：python scripts/reindex_docs.py
# ============================================================================

import sys
import os

# 将项目根目录加入 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models.document import Document, DocumentChunk
from services.vector_service import vector_service
from utils import db


def reindex_all_documents():
    """
    重新索引所有状态为 ready 的文档到 Chroma 向量数据库
    先清空已有向量数据再重建
    """
    with app.app_context():
        print("=" * 60)
        print("  开始重新索引文档到 Chroma 向量数据库")
        print("=" * 60)

        # 1. 获取所有 ready 状态的文档
        docs = Document.query.filter_by(status='ready').all()
        print(f"找到 {len(docs)} 个已就绪文档")

        if not docs:
            print("没有需要索引的文档")
            return

        # 2. 清空旧的分块记录
        for doc in docs:
            old_chunks = DocumentChunk.query.filter_by(document_id=doc.id).all()
            old_ids = [c.vector_id for c in old_chunks if c.vector_id]
            if old_ids:
                print(f"  删除文档 '{doc.title}' 的 {len(old_ids)} 个旧向量...")
                vector_service.delete_document(old_ids)
            for chunk in old_chunks:
                db.session.delete(chunk)
            doc.status = 'processing'
            doc.chunk_count = 0
        db.session.commit()

        # 3. 逐个文档重新向量化
        success_count = 0
        for doc in docs:
            content = doc.content_text
            if not content:
                print(f"  ✗ 文档 '{doc.title}' 无文本内容，跳过")
                doc.status = 'failed'
                doc.error_message = '无文本内容'
                db.session.commit()
                continue

            try:
                print(f"\n  处理文档: {doc.title}...")
                chunks = vector_service.add_document(doc.id, doc.title, content)

                # 保存分块信息
                for chunk_data in chunks:
                    doc_chunk = DocumentChunk(
                        document_id=doc.id,
                        chunk_index=chunk_data['chunk_index'],
                        content=chunk_data['content'],
                        vector_id=chunk_data.get('vector_id', ''),
                        token_count=len(chunk_data['content']),
                    )
                    db.session.add(doc_chunk)

                doc.status = 'ready'
                doc.chunk_count = len(chunks)
                doc.error_message = None
                db.session.commit()
                success_count += 1
                print(f"  ✓ 成功: {len(chunks)} 个文本块")

            except Exception as e:
                db.session.rollback()
                doc.status = 'failed'
                doc.error_message = str(e)
                db.session.commit()
                print(f"  ✗ 失败: {e}")

        # 4. 统计结果
        total_vectors = vector_service.get_document_count()
        print(f"\n{'=' * 60}")
        print(f"  索引完成!")
        print(f"  成功: {success_count}/{len(docs)} 个文档")
        print(f"  向量总数: {total_vectors}")
        print(f"{'=' * 60}")


if __name__ == '__main__':
    reindex_all_documents()
