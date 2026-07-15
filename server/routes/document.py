# ============================================================================
# 企业知识库 RAG 问答系统 - 文档管理路由
# 功能：文档的上传、列表、删除、分类管理
# ============================================================================

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.document import Document, Category, DocumentChunk
from services.document_service import document_service
from services.vector_service import vector_service
from services.cache_service import cache_service
from utils import db
import os
from werkzeug.utils import secure_filename
import uuid
from sqlalchemy import or_

# 创建文档管理蓝图
document_bp = Blueprint('document', __name__, url_prefix='/api/documents')


@document_bp.route('', methods=['GET'])
@jwt_required()
def get_documents():
    """
    获取文档列表（支持分页和筛选）
    查询参数: page, per_page, status, category_id, keyword
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    category_id = request.args.get('category_id', type=int)
    keyword = request.args.get('keyword', '').strip()

    # 构建查询
    query = Document.query

    if status:
        query = query.filter(Document.status == status)
    if category_id:
        query = query.filter(Document.category_id == category_id)
    if keyword:
        query = query.filter(
            db.or_(
                Document.title.ilike(f'%{keyword}%'),
                Document.summary.ilike(f'%{keyword}%'),
            )
        )

    # 按创建时间降序排列
    query = query.order_by(Document.created_at.desc())

    # 分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    docs = [doc.to_dict() for doc in pagination.items]

    return jsonify({
        'code': 200,
        'data': {
            'list': docs,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages,
        },
        'message': '获取成功',
    })


@document_bp.route('/<int:doc_id>', methods=['GET'])
@jwt_required()
def get_document_detail(doc_id: int):
    """
    获取文档详情
    Args:
        doc_id: 文档ID
    """
    doc = Document.query.get(doc_id)
    if not doc:
        return jsonify({'code': 404, 'data': None, 'message': '文档不存在'}), 404

    return jsonify({'code': 200, 'data': doc.to_dict(), 'message': '获取成功'})


@document_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_document():
    """
    上传并处理文档
    接收 multipart/form-data: file(文件), title(标题), category_id(分类ID)
    """
    user_id = int(get_jwt_identity())

    # 检查是否有文件
    if 'file' not in request.files:
        return jsonify({'code': 400, 'data': None, 'message': '请选择文件'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 400, 'data': None, 'message': '文件名为空'}), 400

    # 检查文件类型
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in document_service.SUPPORTED_EXTENSIONS:
        return jsonify({
            'code': 400,
            'data': None,
            'message': f'不支持的文件类型: {ext}，仅支持: {", ".join(document_service.SUPPORTED_EXTENSIONS.keys())}'
        }), 400

    file_type = document_service.SUPPORTED_EXTENSIONS[ext]
    title = request.form.get('title', '').strip() or os.path.splitext(file.filename)[0]
    category_id = request.form.get('category_id', type=int)

    try:
        # 1. 保存文件到本地
        safe_filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
        file_path = os.path.join(document_service.UPLOAD_DIR, safe_filename)
        file.save(file_path)
        file_size = os.path.getsize(file_path)

        # 2. 提取文本内容
        content_text = document_service.extract_text(file_path, file_type)

        # 3. 创建文档记录（状态为 processing）
        doc = Document(
            title=title,
            file_name=file.filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            content_text='',
            summary='',
            category_id=category_id,
            uploaded_by=user_id,
            status='processing',  # 初始状态为处理中
        )
        db.session.add(doc)
        db.session.commit()

        # 4. 异步处理文档向量化（这里同步执行以便返回结果）
        success = document_service.process_document(doc.id, title, content_text)

        if success:
            # 清除问答和向量缓存，因为知识库内容已更新
            cache_service.invalidate_qa_cache()
            cache_service.invalidate_vector_cache()
            return jsonify({
                'code': 200,
                'data': doc.to_dict(),
                'message': '文档上传并处理成功',
            })
        else:
            return jsonify({
                'code': 500,
                'data': None,
                'message': '文档向量化处理失败',
            }), 500

    except Exception as e:
        print(f"[文档路由] 上传失败: {e}")
        return jsonify({'code': 500, 'data': None, 'message': f'上传失败: {str(e)}'}), 500


@document_bp.route('/<int:doc_id>', methods=['DELETE'])
@jwt_required()
def delete_document(doc_id: int):
    """
    删除文档（同时删除向量数据库中的向量和本地文件）
    Args:
        doc_id: 文档ID
    """
    doc = Document.query.get(doc_id)
    if not doc:
        return jsonify({'code': 404, 'data': None, 'message': '文档不存在'}), 404

    try:
        # 1. 收集所有向量ID
        vector_ids = [chunk.vector_id for chunk in doc.chunks if chunk.vector_id]

        # 2. 从 Chroma 删除向量
        if vector_ids:
            vector_service.delete_document(vector_ids)

        # 3. 删除本地文件
        if doc.file_path and os.path.exists(doc.file_path):
            os.remove(doc.file_path)

        # 4. 删除数据库记录（级联删除 chunks）
        db.session.delete(doc)
        db.session.commit()

        # 5. 清除相关缓存（文档变更后，问答和向量缓存失效）
        cache_service.invalidate_qa_cache()
        cache_service.invalidate_vector_cache()

        return jsonify({'code': 200, 'data': None, 'message': '文档已删除'})

    except Exception as e:
        db.session.rollback()
        print(f"[文档路由] 删除失败: {e}")
        return jsonify({'code': 500, 'data': None, 'message': f'删除失败: {str(e)}'}), 500


@document_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """
    获取所有文档分类列表（带缓存）
    """
    # 尝试从缓存获取
    cached = cache_service.get_categories_cache()
    if cached is not None:
        return jsonify({'code': 200, 'data': cached, 'message': '获取成功（缓存）'})

    categories = Category.query.order_by(Category.sort_order).all()
    data = [cat.to_dict() for cat in categories]

    # 存入缓存
    cache_service.set_categories_cache(data)

    return jsonify({
        'code': 200,
        'data': data,
        'message': '获取成功',
    })


@document_bp.route('/categories', methods=['POST'])
@jwt_required()
def create_category():
    """
    创建新的文档分类（仅管理员）
    """
    from flask_jwt_extended import get_jwt
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'code': 403, 'data': None, 'message': '仅管理员可创建分类'}), 403

    data = request.get_json()
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'code': 400, 'data': None, 'message': '分类名称不能为空'}), 400

    # 检查是否已存在
    if Category.query.filter_by(name=name).first():
        return jsonify({'code': 409, 'data': None, 'message': '分类名称已存在'}), 409

    category = Category(
        name=name,
        description=data.get('description', ''),
        parent_id=data.get('parent_id'),
        sort_order=data.get('sort_order', 0),
    )
    db.session.add(category)
    db.session.commit()

    return jsonify({'code': 200, 'data': category.to_dict(), 'message': '创建成功'})


@document_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
@jwt_required()
def delete_category(cat_id: int):
    """删除分类（仅管理员）"""
    from flask_jwt_extended import get_jwt
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'code': 403, 'data': None, 'message': '仅管理员可删除分类'}), 403

    category = Category.query.get(cat_id)
    if not category:
        return jsonify({'code': 404, 'data': None, 'message': '分类不存在'}), 404

    if category.documents.filter(Document.status == 'ready').count() > 0:
        return jsonify({'code': 400, 'data': None, 'message': '该分类下还有文档，无法删除'}), 400

    db.session.delete(category)
    db.session.commit()

    return jsonify({'code': 200, 'data': None, 'message': '删除成功'})


@document_bp.route('/search', methods=['GET'])
@jwt_required()
def search_documents():
    """
    全文搜索知识库文档（混合搜索：关键词 + 向量语义）
    查询参数: q, page, per_page, category_id
    """
    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    category_id = request.args.get('category_id', type=int)

    if not q:
        return jsonify({'code': 400, 'data': None, 'message': '搜索关键词不能为空'}), 400

    try:
        # 1. 关键词搜索（从 MySQL 全文搜索）
        keyword_query = Document.query.filter(
            Document.status == 'ready'
        ).filter(
            or_(
                Document.title.ilike(f'%{q}%'),
                Document.content_text.ilike(f'%{q}%'),
                Document.summary.ilike(f'%{q}%'),
            )
        )
        if category_id:
            keyword_query = keyword_query.filter(Document.category_id == category_id)

        keyword_results = keyword_query.order_by(Document.created_at.desc()).all()

        # 2. 向量语义搜索
        try:
            semantic_chunks = vector_service.similarity_search(q, k=3)
            semantic_doc_ids = set()
            for chunk in semantic_chunks:
                doc_id = chunk['metadata'].get('doc_id')
                if doc_id:
                    semantic_doc_ids.add(int(doc_id))

            semantic_docs = []
            for doc_id in semantic_doc_ids:
                doc = Document.query.get(doc_id)
                if doc and doc.status == 'ready':
                    semantic_docs.append(doc.to_dict())
        except Exception as e:
            print(f"[文档路由] 语义搜索失败: {e}")
            semantic_docs = []

        # 3. 合并结果（去重）
        seen_ids = set()
        merged = []

        # 关键词结果优先
        for doc in keyword_results:
            if doc.id not in seen_ids:
                seen_ids.add(doc.id)
                merged.append(doc.to_dict())

        # 补充语义搜索结果
        for doc in semantic_docs:
            if doc['id'] not in seen_ids:
                seen_ids.add(doc['id'])
                doc['_semantic'] = True
                merged.append(doc)

        # 分页
        total = len(merged)
        start = (page - 1) * per_page
        end = start + per_page
        page_items = merged[start:end]

        return jsonify({
            'code': 200,
            'data': {
                'list': page_items,
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page,
                'keyword': q,
            },
            'message': '搜索完成',
        })

    except Exception as e:
        print(f"[文档路由] 搜索失败: {e}")
        return jsonify({'code': 500, 'data': None, 'message': f'搜索失败: {str(e)}'}), 500


@document_bp.route('/<int:doc_id>/content', methods=['GET'])
@jwt_required()
def get_document_content(doc_id: int):
    """
    获取文档完整内容（用于预览）
    Args:
        doc_id: 文档ID
    """
    doc = Document.query.get(doc_id)
    if not doc:
        return jsonify({'code': 404, 'data': None, 'message': '文档不存在'}), 404

    # 获取文档块
    chunks = DocumentChunk.query.filter_by(document_id=doc_id).order_by(
        DocumentChunk.chunk_index
    ).all()

    return jsonify({
        'code': 200,
        'data': {
            'id': doc.id,
            'title': doc.title,
            'content_text': doc.content_text,
            'summary': doc.summary,
            'chunks': [c.to_dict() for c in chunks],
            'file_type': doc.file_type,
            'file_name': doc.file_name,
            'created_at': doc.created_at.isoformat() if doc.created_at else None,
        },
        'message': '获取成功',
    })
