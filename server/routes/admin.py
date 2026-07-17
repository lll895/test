# ============================================================================
# 企业知识库 RAG 问答系统 - 管理员后台路由
# 功能：仪表盘统计数据、用户管理、系统管理
# ============================================================================

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models.user import User
from models.document import Document, Category
from models.qa_log import QaLog
from models.announcement import Announcement
from models.knowledge_gap import KnowledgeGap
from services.vector_service import vector_service
from services.cache_service import cache_service
from utils import db
from utils.logger import get_logger
from datetime import datetime, timedelta
from sqlalchemy import func

logger = get_logger(__name__)

# 创建管理员蓝图
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


def admin_required():
    """
    管理员权限装饰器
    检查当前用户是否为管理员
    """
    def decorator(f):
        from functools import wraps

        @wraps(f)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims.get('role') != 'admin':
                return jsonify({'code': 403, 'data': None, 'message': '需要管理员权限'}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator


@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@admin_required()
def get_dashboard():
    """
    获取管理后台首页统计数据（带 Redis 缓存）
    缓存时间 5 分钟，减少重复数据库查询
    """
    # 尝试从缓存获取
    cached = cache_service.get_dashboard_cache()
    if cached:
        return jsonify({'code': 200, 'data': cached, 'message': '获取成功（缓存）'})

    # 用户统计
    total_users = User.query.count()
    admin_count = User.query.filter_by(role='admin').count()
    today_new_users = User.query.filter(
        User.created_at >= datetime.now().replace(hour=0, minute=0, second=0)
    ).count()

    # 文档统计
    total_docs = Document.query.count()
    ready_docs = Document.query.filter_by(status='ready').count()
    processing_docs = Document.query.filter_by(status='processing').count()
    failed_docs = Document.query.filter_by(status='failed').count()
    total_chunks = db.session.query(
        func.sum(Document.chunk_count)
    ).scalar() or 0

    # 向量数量
    vector_count = vector_service.get_document_count()

    # 问答统计
    total_qa = QaLog.query.count()
    today_qa = QaLog.query.filter(
        QaLog.created_at >= datetime.now().replace(hour=0, minute=0, second=0)
    ).count()
    useful_feedback = QaLog.query.filter_by(feedback=1).count()
    useless_feedback = QaLog.query.filter_by(feedback=0).count()

    # 分类统计（文档数前5）
    categories_stats = db.session.query(
        Category.name,
        func.count(Document.id).label('doc_count')
    ).outerjoin(Document, Document.category_id == Category.id
    ).group_by(Category.id, Category.name
    ).order_by(func.count(Document.id).desc()
    ).limit(5).all()

    # 近7天问答趋势
    seven_days_ago = datetime.now() - timedelta(days=7)
    qa_trend = db.session.query(
        func.date(QaLog.created_at).label('date'),
        func.count(QaLog.id).label('count'),
    ).filter(QaLog.created_at >= seven_days_ago
    ).group_by(func.date(QaLog.created_at)
    ).order_by(func.date(QaLog.created_at)).all()

    # 填充近7天数据（没有数据的日期补0）
    trend_data = []
    for i in range(6, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime('%m-%d')
        count = 0
        for row in qa_trend:
            if row.date.strftime('%m-%d') == day:
                count = row.count
                break
        trend_data.append({'date': day, 'count': count})

    # 用户角色分布
    role_distribution = [
        {'name': '管理员', 'value': admin_count},
        {'name': '普通用户', 'value': total_users - admin_count},
    ]

    # 文档状态分布
    status_distribution = [
        {'name': '已完成', 'value': ready_docs},
        {'name': '处理中', 'value': processing_docs},
        {'name': '失败', 'value': failed_docs},
    ]

    dashboard_data = {
        # 概要统计
        'summary': {
            'total_users': total_users,
            'total_docs': total_docs,
            'ready_docs': ready_docs,
            'total_qa': total_qa,
            'today_qa': today_qa,
            'today_new_users': today_new_users,
            'vector_count': vector_count,
            'total_chunks': total_chunks,
        },
        # 问答趋势（近7天）
        'qa_trend': trend_data,
        # 分类文档数量 TOP5
        'category_stats': [
            {'name': row.name, 'doc_count': row.doc_count}
            for row in categories_stats
        ],
        # 用户角色分布
        'role_distribution': role_distribution,
        # 文档状态分布
        'status_distribution': status_distribution,
        # 反馈统计
        'feedback_stats': {
            'useful': useful_feedback,
            'useless': useless_feedback,
            'total': total_qa,
        },
    }

    # 写入缓存
    cache_service.set_dashboard_cache(dashboard_data)

    return jsonify({
        'code': 200,
        'data': dashboard_data,
        'message': '获取成功',
    })


@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required()
def get_users():
    """
    获取用户列表（分页）
    查询参数: page, per_page, role, keyword
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    role = request.args.get('role')
    keyword = request.args.get('keyword', '').strip()

    query = User.query
    if role:
        query = query.filter(User.role == role)
    if keyword:
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{keyword}%'),
                User.real_name.ilike(f'%{keyword}%'),
                User.email.ilike(f'%{keyword}%'),
            )
        )

    query = query.order_by(User.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'code': 200,
        'data': {
            'list': [u.to_dict() for u in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages,
        },
        'message': '获取成功',
    })


@admin_bp.route('/users/<int:user_id>/status', methods=['PUT'])
@jwt_required()
@admin_required()
def toggle_user_status(user_id: int):
    """
    启用/禁用用户账号
    Args:
        user_id: 用户ID
    """
    if user_id == int(get_jwt_identity()):
        return jsonify({'code': 400, 'data': None, 'message': '不能禁用自己'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'code': 404, 'data': None, 'message': '用户不存在'}), 404

    user.status = not user.status
    db.session.commit()

    return jsonify({
        'code': 200,
        'data': {'id': user.id, 'status': user.status},
        'message': '操作成功',
    })


@admin_bp.route('/announcements', methods=['GET'])
@jwt_required()
def get_announcements():
    """
    获取公告列表（所有登录用户可看）
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    query = Announcement.query.filter_by(is_active=True).order_by(
        Announcement.priority.desc(),
        Announcement.created_at.desc()
    )
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'code': 200,
        'data': {
            'list': [a.to_dict() for a in pagination.items],
            'total': pagination.total,
        },
        'message': '获取成功',
    })


@admin_bp.route('/announcements', methods=['POST'])
@jwt_required()
@admin_required()
def create_announcement():
    """
    发布公告（仅管理员）
    """
    data = request.get_json()
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    priority = data.get('priority', 'normal')

    if not title or not content:
        return jsonify({'code': 400, 'data': None, 'message': '标题和内容不能为空'}), 400

    user_id = int(get_jwt_identity())
    announcement = Announcement(
        title=title,
        content=content,
        priority=priority if priority in ('low', 'normal', 'high') else 'normal',
        published_by=user_id,
    )
    db.session.add(announcement)
    db.session.commit()

    return jsonify({'code': 200, 'data': announcement.to_dict(), 'message': '发布成功'})


@admin_bp.route('/announcements/<int:ann_id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_announcement(ann_id: int):
    """删除公告（仅管理员）"""
    announcement = Announcement.query.get(ann_id)
    if not announcement:
        return jsonify({'code': 404, 'data': None, 'message': '公告不存在'}), 404

    db.session.delete(announcement)
    db.session.commit()

    return jsonify({'code': 200, 'data': None, 'message': '删除成功'})


# ==================== 知识盲区分析 ====================

@admin_bp.route('/knowledge-gaps', methods=['GET'])
@jwt_required()
@admin_required()
def get_knowledge_gaps():
    """
    获取知识盲区统计（未在知识库中找到答案的问题）
    查询参数: days (最近N天), page, per_page
    """
    days = request.args.get('days', 30, type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    from datetime import datetime, timedelta
    since = datetime.now() - timedelta(days=days)

    query = KnowledgeGap.query.filter(
        KnowledgeGap.last_asked >= since
    ).order_by(KnowledgeGap.hit_count.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # 汇总统计
    total_gaps = query.count()
    total_questions = db.session.query(
        func.sum(KnowledgeGap.hit_count)
    ).filter(KnowledgeGap.last_asked >= since).scalar() or 0

    # 高频关键词提取
    all_questions = [g.question for g in query.limit(100).all()]
    keywords = {}
    stop_words = {'的', '了', '是', '在', '有', '我', '怎么', '如何', '什么', '哪个', '可以', '吗', '啊', '呢', '吧'}
    for q in all_questions:
        for word in q.split():
            word = word.strip('？?!！，。、').lower()
            if word and len(word) > 1 and word not in stop_words:
                keywords[word] = keywords.get(word, 0) + 1
    top_keywords = sorted(keywords.items(), key=lambda x: -x[1])[:20]

    return jsonify({
        'code': 200,
        'data': {
            'list': [g.to_dict() for g in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'summary': {
                'total_gaps': total_gaps,
                'total_questions': total_questions,
                'top_keywords': [{'word': k, 'count': v} for k, v in top_keywords],
            },
        },
        'message': '获取成功',
    })
