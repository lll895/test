# ============================================================================
# 企业知识库 RAG 问答系统 - 收藏夹路由
# 功能：收藏问答/文档，添加笔记，管理收藏
# ============================================================================

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.bookmark import Bookmark
from models.qa_log import QaLog
from models.document import Document
from utils import db
import hashlib

bookmark_bp = Blueprint('bookmark', __name__, url_prefix='/api/bookmarks')


@bookmark_bp.route('', methods=['GET'])
@jwt_required()
def list_bookmarks():
    """获取当前用户的所有收藏（分页）"""
    user_id = int(get_jwt_identity())
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    btype = request.args.get('type')  # 可选：qa / document

    query = Bookmark.query.filter_by(user_id=user_id).order_by(Bookmark.created_at.desc())
    if btype:
        query = query.filter(Bookmark.type == btype)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    items = []
    for bm in pagination.items:
        d = bm.to_dict()
        # 附带目标信息
        if bm.type == 'qa':
            qa = QaLog.query.get(bm.target_id)
            d['target_title'] = qa.question[:100] if qa else '(已删除)'
            d['target_preview'] = qa.answer[:200] if qa else ''
        elif bm.type == 'document':
            doc = Document.query.get(bm.target_id)
            d['target_title'] = doc.title if doc else '(已删除)'
            d['target_preview'] = doc.summary[:200] if doc and doc.summary else ''
        items.append(d)

    return jsonify({
        'code': 200,
        'data': {
            'list': items,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages,
        },
        'message': '获取成功',
    })


@bookmark_bp.route('', methods=['POST'])
@jwt_required()
def add_bookmark():
    """添加收藏"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    btype = data.get('type')     # qa / document
    target_id = data.get('target_id')
    note = data.get('note', '')

    if btype not in ('qa', 'document') or not target_id:
        return jsonify({'code': 400, 'data': None, 'message': '参数错误'}), 400

    # 检查是否已收藏
    existing = Bookmark.query.filter_by(
        user_id=user_id, type=btype, target_id=int(target_id)
    ).first()
    if existing:
        return jsonify({'code': 409, 'data': existing.to_dict(), 'message': '已收藏'}), 409

    # 验证目标存在
    if btype == 'qa':
        obj = QaLog.query.get(int(target_id))
    else:
        obj = Document.query.get(int(target_id))
    if not obj:
        return jsonify({'code': 404, 'data': None, 'message': '目标不存在'}), 404

    bm = Bookmark(user_id=user_id, type=btype, target_id=int(target_id), note=note)
    db.session.add(bm)
    db.session.commit()

    return jsonify({'code': 200, 'data': bm.to_dict(), 'message': '收藏成功'})


@bookmark_bp.route('/<int:bookmark_id>', methods=['DELETE'])
@jwt_required()
def delete_bookmark(bookmark_id: int):
    """删除收藏"""
    user_id = int(get_jwt_identity())
    bm = Bookmark.query.filter_by(id=bookmark_id, user_id=user_id).first()
    if not bm:
        return jsonify({'code': 404, 'data': None, 'message': '收藏不存在'}), 404
    db.session.delete(bm)
    db.session.commit()
    return jsonify({'code': 200, 'data': None, 'message': '已取消收藏'})


@bookmark_bp.route('/<int:bookmark_id>/note', methods=['PUT'])
@jwt_required()
def update_note(bookmark_id: int):
    """更新笔记"""
    user_id = int(get_jwt_identity())
    bm = Bookmark.query.filter_by(id=bookmark_id, user_id=user_id).first()
    if not bm:
        return jsonify({'code': 404, 'data': None, 'message': '收藏不存在'}), 404
    data = request.get_json()
    bm.note = data.get('note', '')
    db.session.commit()
    return jsonify({'code': 200, 'data': bm.to_dict(), 'message': '笔记已更新'})


@bookmark_bp.route('/check', methods=['GET'])
@jwt_required()
def check_bookmark():
    """检查是否已收藏"""
    user_id = int(get_jwt_identity())
    btype = request.args.get('type')
    target_id = request.args.get('target_id', type=int)
    if not btype or not target_id:
        return jsonify({'code': 400, 'data': None, 'message': '参数错误'}), 400

    bm = Bookmark.query.filter_by(
        user_id=user_id, type=btype, target_id=target_id
    ).first()

    return jsonify({
        'code': 200,
        'data': {'bookmarked': bm is not None, 'bookmark': bm.to_dict() if bm else None},
        'message': '查询成功',
    })
