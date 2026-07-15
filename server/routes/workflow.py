# ============================================================================
# 企业知识库 RAG 问答系统 - 工作流审批路由
# 功能：管理操作按钮配置，根据关键词匹配返回可执行操作
# ============================================================================

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models.workflow import WorkflowAction
from utils import db

workflow_bp = Blueprint('workflow', __name__, url_prefix='/api/workflow')


def admin_required():
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims.get('role') != 'admin':
                return jsonify({'code': 403, 'data': None, 'message': '需要管理员权限'}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


@workflow_bp.route('/actions', methods=['GET'])
@jwt_required()
def get_actions():
    """获取所有启用的操作按钮"""
    actions = WorkflowAction.query.filter_by(is_active=True).order_by(
        WorkflowAction.sort_order).all()
    return jsonify({
        'code': 200,
        'data': [a.to_dict() for a in actions],
        'message': '获取成功',
    })


@workflow_bp.route('/match', methods=['POST'])
@jwt_required()
def match_actions():
    """
    根据问题/回答匹配对应的操作按钮
    请求体: {"question": "xxx", "answer": "xxx"}
    返回: 匹配到的操作按钮列表
    """
    data = request.get_json()
    text = (data.get('question', '') + ' ' + data.get('answer', '')).lower()

    actions = WorkflowAction.query.filter_by(is_active=True).order_by(
        WorkflowAction.sort_order).all()

    matched = []
    for action in actions:
        keywords = [k.strip().lower() for k in action.keywords.split(',')]
        if any(kw in text for kw in keywords):
            matched.append(action.to_dict())

    return jsonify({'code': 200, 'data': matched, 'message': '匹配完成'})


# ===== 管理员 CRUD =====

@workflow_bp.route('/actions', methods=['POST'])
@jwt_required()
@admin_required()
def create_action():
    """创建操作按钮"""
    data = request.get_json()
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'code': 400, 'data': None, 'message': '名称不能为空'}), 400
    action = WorkflowAction(
        name=name,
        keywords=data.get('keywords', ''),
        label=data.get('label', name),
        url=data.get('url', ''),
        icon=data.get('icon', 'Link'),
        description=data.get('description', ''),
        sort_order=data.get('sort_order', 0),
    )
    db.session.add(action)
    db.session.commit()
    return jsonify({'code': 200, 'data': action.to_dict(), 'message': '创建成功'})


@workflow_bp.route('/actions/<int:action_id>', methods=['PUT'])
@jwt_required()
@admin_required()
def update_action(action_id: int):
    """更新操作按钮"""
    action = WorkflowAction.query.get(action_id)
    if not action:
        return jsonify({'code': 404, 'data': None, 'message': '不存在'}), 404
    data = request.get_json()
    for field in ('name', 'keywords', 'label', 'url', 'icon', 'description', 'sort_order', 'is_active'):
        if field in data:
            setattr(action, field, data[field])
    db.session.commit()
    return jsonify({'code': 200, 'data': action.to_dict(), 'message': '更新成功'})


@workflow_bp.route('/actions/<int:action_id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_action(action_id: int):
    """删除操作按钮"""
    action = WorkflowAction.query.get(action_id)
    if not action:
        return jsonify({'code': 404, 'data': None, 'message': '不存在'}), 404
    db.session.delete(action)
    db.session.commit()
    return jsonify({'code': 200, 'data': None, 'message': '删除成功'})
