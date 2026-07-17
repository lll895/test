# ============================================================================
# 企业知识库 RAG 问答系统 - 问答交互路由（升级版）
# 功能：智能问答、流式响应、多轮对话、对话历史管理
# ============================================================================

from flask import Blueprint, request, jsonify, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.qa_log import QaLog
from models.conversation import Conversation, ConversationMessage
from services.rag_service import rag_service
from services.cache_service import cache_service
from utils import db
from utils.logger import get_logger
import json
import uuid
import time

logger = get_logger(__name__)

# 创建问答蓝图
qa_bp = Blueprint('qa', __name__, url_prefix='/api/qa')

# ==================== 对话会话管理 ====================

@qa_bp.route('/session/start', methods=['POST'])
@jwt_required()
def start_session():
    """
    开始一个新的对话会话
    返回唯一的 session_id，用于多轮对话上下文管理
    """
    session_id = str(uuid.uuid4())
    return jsonify({
        'code': 200,
        'data': {'session_id': session_id},
        'message': '对话已创建',
    })


@qa_bp.route('/session/<session_id>/clear', methods=['POST'])
@jwt_required()
def clear_session(session_id: str):
    """清除指定会话的对话历史"""
    cache_service.clear_conversation(session_id)
    return jsonify({'code': 200, 'data': None, 'message': '对话已重置'})


# ==================== 标准问答（带缓存支持）====================

@qa_bp.route('/ask', methods=['POST'])
@jwt_required()
def ask_question():
    """
    向知识库提问（升级版）
    支持多轮对话上下文
    请求体: {"question": "xxx", "session_id": "xxx"}
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    question = data.get('question', '').strip()
    session_id = data.get('session_id')

    if not question:
        return jsonify({'code': 400, 'data': None, 'message': '问题不能为空'}), 400

    if len(question) > 2000:
        return jsonify({'code': 400, 'data': None, 'message': '问题长度不能超过2000字'}), 400

    start_time = time.time()

    try:
        # 执行 RAG 问答（传入 session_id 以支持多轮对话上下文）
        result = rag_service.query(question, session_id=session_id)

        # 保存问答记录到数据库
        qa_log = QaLog(
            user_id=user_id,
            question=question,
            answer=result['answer'],
            sources=json.dumps(result['sources'], ensure_ascii=False),
            model_used=result.get('model_used'),
            embedding_model=result.get('embedding_model'),
            chunks_retrieved=result['chunks_retrieved'],
            cost_time_ms=result['cost_time_ms'],
            feedback=-1,
        )
        db.session.add(qa_log)
        db.session.commit()

        # 记录缓存命中状态
        cache_hit = result.get('from_cache', False)

        return jsonify({
            'code': 200,
            'data': {
                'qa_id': qa_log.id,
                'answer': result['answer'],
                'sources': result['sources'],
                'chunks_retrieved': result['chunks_retrieved'],
                'cost_time_ms': result['cost_time_ms'],
                'model_used': result.get('model_used'),
                'from_cache': cache_hit,
            },
            'message': '回答完成',
        })

    except Exception as e:
        logger.error(f"处理失败: {e}")
        return jsonify({'code': 500, 'data': None, 'message': f'问答处理失败: {str(e)}'}), 500


# ==================== 流式问答（SSE） ====================

@qa_bp.route('/ask/stream', methods=['POST'])
@jwt_required()
def ask_question_stream():
    """
    流式问答接口（SSE - Server-Sent Events）
    支持逐字输出回答，提升用户体验
    请求体: {"question": "xxx", "session_id": "xxx"}
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    question = data.get('question', '').strip()
    session_id = data.get('session_id')

    if not question:
        return jsonify({'code': 400, 'data': None, 'message': '问题不能为空'}), 400

    if len(question) > 2000:
        return jsonify({'code': 400, 'data': None, 'message': '问题长度不能超过2000字'}), 400

    def generate():
        full_answer = ""
        sources_data = []
        chunks_count = 0

        try:
            # 1. 发送开始信号
            yield f"data: {json.dumps({'type': 'start'})}\n\n"

            # 2. 检查缓存
            cached = cache_service.get_qa_cache(question)
            if cached:
                yield f"data: {json.dumps({'type': 'sources', 'sources': cached.get('sources', []), 'chunks': cached.get('chunks_retrieved', 0)}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'text', 'content': cached['answer']}, ensure_ascii=False)}\n\n"
                full_answer = cached['answer']
                elapsed = cached.get('cost_time_ms', 0)
                # 保存到数据库
                qa_log = QaLog(
                    user_id=user_id, question=question, answer=full_answer,
                    sources=json.dumps(cached.get('sources', []), ensure_ascii=False),
                    model_used=rag_service.model_used,
                    chunks_retrieved=cached.get('chunks_retrieved', 0),
                    cost_time_ms=elapsed, feedback=-1,
                )
                db.session.add(qa_log)
                db.session.commit()
                yield f"data: {json.dumps({'type': 'done', 'qa_id': qa_log.id, 'cost_time_ms': elapsed, 'from_cache': True}, ensure_ascii=False)}\n\n"
                return

            # 3. 向量检索
            from services.vector_service import vector_service
            import time as time_module
            search_start = time_module.time()

            relevant_chunks = vector_service.similarity_search(question)
            chunks_count = len(relevant_chunks)

            context_parts = []
            seen_docs = set()

            if relevant_chunks:
                for chunk in relevant_chunks:
                    metadata = chunk['metadata']
                    doc_title = metadata.get('title', '未知文档')
                    context_parts.append(chunk['content'])
                    if doc_title not in seen_docs:
                        seen_docs.add(doc_title)
                        sources_data.append({
                            'title': doc_title,
                            'doc_id': metadata.get('doc_id'),
                            'content': chunk['content'][:300] + '...' if len(chunk['content']) > 300 else chunk['content'],
                            'similarity': chunk['similarity_score'],
                        })

            context = "\n\n---\n\n".join(context_parts)

            # 先发送来源（让前端提前展示）
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources_data, 'chunks': chunks_count}, ensure_ascii=False)}\n\n"
            # 确保来源信息先刷出去
            import sys as _sys
            _sys.stdout.flush()

            # 4. 获取对话历史
            conversation_history = cache_service.get_conversation_context(session_id) if session_id else []

            # 5. 流式生成回答
            from services.llm_service import LLMService, llm_service as _llm
            social_type = LLMService._is_greeting(question)
            if social_type:
                greeting = LLMService._get_greeting_response(social_type)
                yield f"data: {json.dumps({'type': 'text', 'content': greeting}, ensure_ascii=False)}\n\n"
                full_answer = greeting
            else:
                for chunk in _llm.generate_stream(question, context, conversation_history):
                    full_answer += chunk
                    yield f"data: {json.dumps({'type': 'text', 'content': chunk}, ensure_ascii=False)}\n\n"

            elapsed = int((time_module.time() - search_start) * 1000)

            # 6. 保存到数据库（直接使用当前请求上下文）
            qa_log = QaLog(
                user_id=user_id, question=question, answer=full_answer,
                sources=json.dumps(sources_data, ensure_ascii=False),
                model_used=rag_service.model_used,
                chunks_retrieved=chunks_count,
                cost_time_ms=elapsed, feedback=-1,
            )
            db.session.add(qa_log)
            db.session.commit()
            qa_id = qa_log.id

            # 7. 保存对话上下文和缓存
            if session_id:
                cache_service.append_conversation(session_id, "user", question)
                cache_service.append_conversation(session_id, "assistant", full_answer)
            cache_service.set_qa_cache(question, {
                'answer': full_answer, 'sources': sources_data,
                'chunks_retrieved': chunks_count, 'cost_time_ms': elapsed,
            })

            # 8. 完成信号
            yield f"data: {json.dumps({'type': 'done', 'qa_id': qa_id, 'cost_time_ms': elapsed}, ensure_ascii=False)}\n\n"

        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = f"抱歉，回答过程中出现了问题: {str(e)}"
            yield f"data: {json.dumps({'type': 'error', 'content': error_msg}, ensure_ascii=False)}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache, no-transform',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
            'Access-Control-Allow-Origin': '*',
        }
    )


# ==================== 获取对话历史 ====================

@qa_bp.route('/session/<session_id>/history', methods=['GET'])
@jwt_required()
def get_session_history(session_id: str):
    """获取当前会话的对话历史"""
    history = cache_service.get_conversation_context(session_id)
    return jsonify({
        'code': 200,
        'data': {'messages': history, 'session_id': session_id},
        'message': '获取成功',
    })


# ==================== 问答历史记录 ====================

@qa_bp.route('/history', methods=['GET'])
@jwt_required()
def get_history():
    """
    获取当前用户的问答历史记录
    查询参数: page, per_page
    """
    user_id = int(get_jwt_identity())
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    try:
        query = QaLog.query.filter_by(user_id=user_id).order_by(QaLog.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        logs = []
        for log in pagination.items:
            try:
                logs.append(log.to_dict())
            except Exception as e:
                logger.error(f"序列化问答记录失败 id={log.id}: {e}")
                logs.append({
                    'id': log.id,
                    'question': log.question[:100] if log.question else '(未知)',
                    'answer': '(数据加载失败)',
                    'created_at': log.created_at.isoformat() if log.created_at else None,
                })

        return jsonify({
            'code': 200,
            'data': {
                'list': logs,
                'total': pagination.total,
                'page': page,
                'per_page': per_page,
                'pages': pagination.pages,
            },
            'message': '获取成功',
        })
    except Exception as e:
        logger.error(f"获取问答历史失败 user_id={user_id}: {e}", exc_info=True)
        return jsonify({'code': 500, 'data': None, 'message': '获取问答历史失败，请稍后再试'}), 500


@qa_bp.route('/history/all', methods=['GET'])
@jwt_required()
def get_all_history():
    """
    获取所有用户的问答历史（仅管理员）
    查询参数: page, per_page, user_id
    """
    from flask_jwt_extended import get_jwt
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({'code': 403, 'data': None, 'message': '无权限访问'}), 403

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    user_id = request.args.get('user_id', type=int)

    query = QaLog.query.order_by(QaLog.created_at.desc())
    if user_id:
        query = query.filter(QaLog.user_id == user_id)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    logs = [log.to_dict() for log in pagination.items]

    return jsonify({
        'code': 200,
        'data': {
            'list': logs,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages,
        },
        'message': '获取成功',
    })


@qa_bp.route('/feedback', methods=['POST'])
@jwt_required()
def submit_feedback():
    """
    提交问答反馈（是否有用）
    ---
    请求体: {"qa_id": 1, "feedback": 1 (有用) / 0 (无用)}
    """
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    qa_id = data.get('qa_id')
    feedback = data.get('feedback')

    if qa_id is not None:
        qa_id = int(qa_id)
    if feedback is not None:
        feedback = int(feedback)

    if not qa_id or feedback not in (0, 1):
        return jsonify({'code': 400, 'data': None, 'message': '参数错误'}), 400

    qa_log = QaLog.query.filter_by(id=qa_id, user_id=user_id).first()
    if not qa_log:
        return jsonify({'code': 404, 'data': None, 'message': '问答记录不存在'}), 404

    qa_log.feedback = feedback
    db.session.commit()

    return jsonify({'code': 200, 'data': None, 'message': '感谢您的反馈！'})


@qa_bp.route('/<int:qa_id>', methods=['GET'])
@jwt_required()
def get_qa_detail(qa_id: int):
    """
    获取问答详情
    Args:
        qa_id: 问答记录ID
    """
    user_id = int(get_jwt_identity())
    qa_log = QaLog.query.filter_by(id=qa_id, user_id=user_id).first()
    if not qa_log:
        return jsonify({'code': 404, 'data': None, 'message': '记录不存在'}), 404

    return jsonify({'code': 200, 'data': qa_log.to_dict(), 'message': '获取成功'})


# ==================== 问答导出 ====================

@qa_bp.route('/export', methods=['GET'])
@jwt_required()
def export_qa_history():
    """
    导出问答历史（Markdown 格式）
    查询参数: days (最近N天)
    """
    user_id = int(get_jwt_identity())
    days = request.args.get('days', 7, type=int)

    from datetime import datetime, timedelta
    since = datetime.now() - timedelta(days=days)

    logs = QaLog.query.filter(
        QaLog.user_id == user_id,
        QaLog.created_at >= since,
    ).order_by(QaLog.created_at.asc()).all()

    if not logs:
        return jsonify({'code': 404, 'data': None, 'message': '没有可导出的问答记录'}), 404

    # 生成 Markdown
    lines = [
        f"# 问答历史导出\n",
        f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        f"**时间范围**: 最近 {days} 天\n",
        f"**问答数量**: {len(logs)} 条\n",
        "---\n",
    ]

    for i, log in enumerate(logs, 1):
        lines.append(f"## {i}. {log.question}")
        lines.append(f"**时间**: {log.created_at.strftime('%Y-%m-%d %H:%M') if log.created_at else '未知'}")
        if log.feedback == 1:
            lines.append("**反馈**: ✅ 有帮助\n")
        elif log.feedback == 0:
            lines.append("**反馈**: ❌ 没帮助\n")
        lines.append(f"\n{log.answer}\n")
        lines.append("---\n")

    content = "\n".join(lines)

    return Response(
        content,
        mimetype='text/markdown; charset=utf-8',
        headers={
            'Content-Disposition': f'attachment; filename=qa_export_{datetime.now().strftime("%Y%m%d")}.md',
            'Content-Type': 'text/markdown; charset=utf-8',
        }
    )


# ==================== 用户个人统计 ====================

@qa_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_user_qa_stats():
    """
    获取当前用户的问答个人统计
    """
    user_id = int(get_jwt_identity())

    from sqlalchemy import func
    from datetime import datetime, timedelta

    # 总问答数
    total = QaLog.query.filter_by(user_id=user_id).count()

    # 今日问答数
    today_start = datetime.now().replace(hour=0, minute=0, second=0)
    today_count = QaLog.query.filter(
        QaLog.user_id == user_id,
        QaLog.created_at >= today_start,
    ).count()

    # 近7天每日问答数
    seven_days_ago = datetime.now() - timedelta(days=7)
    daily_stats = db.session.query(
        func.date(QaLog.created_at).label('date'),
        func.count(QaLog.id).label('count'),
    ).filter(
        QaLog.user_id == user_id,
        QaLog.created_at >= seven_days_ago,
    ).group_by(func.date(QaLog.created_at)).all()

    trend = []
    for i in range(6, -1, -1):
        day = (datetime.now() - timedelta(days=i)).strftime('%m-%d')
        count = 0
        for row in daily_stats:
            if row.date.strftime('%m-%d') == day:
                count = row.count
                break
        trend.append({'date': day, 'count': count})

    # 平均响应时间
    avg_time = db.session.query(
        func.avg(QaLog.cost_time_ms)
    ).filter(
        QaLog.user_id == user_id,
        QaLog.cost_time_ms > 0,
    ).scalar() or 0

    # 有用反馈数
    useful = QaLog.query.filter_by(user_id=user_id, feedback=1).count()

    # 总token使用量（累计）
    total_tokens = db.session.query(
        func.sum(QaLog.tokens_used)
    ).filter(QaLog.user_id == user_id).scalar() or 0

    return jsonify({
        'code': 200,
        'data': {
            'total_qa': total,
            'today_qa': today_count,
            'daily_trend': trend,
            'avg_response_time_ms': round(float(avg_time)),
            'useful_count': useful,
            'useful_rate': round(useful / total * 100, 1) if total > 0 else 0,
            'total_tokens': int(total_tokens),
        },
        'message': '获取成功',
    })


# ==================== 跨设备对话同步 ====================

@qa_bp.route('/session/save', methods=['POST'])
@jwt_required()
def save_session():
    """
    将当前 Redis 对话保存到 MySQL（跨设备同步）
    请求体: {"session_id": "xxx", "title": "可选标题"}
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    session_id = data.get('session_id')
    title = data.get('title')

    if not session_id:
        return jsonify({'code': 400, 'data': None, 'message': '缺少 session_id'}), 400

    messages = cache_service.get_conversation_context(session_id)

    # 如果 Redis 没有数据，尝试从 qa_logs 重建最近对话
    if not messages:
        recent_logs = QaLog.query.filter_by(user_id=user_id).order_by(
            QaLog.created_at.desc()).limit(10).all()
        if recent_logs:
            messages = []
            for log in reversed(recent_logs):
                messages.append({'role': 'user', 'content': log.question})
                messages.append({'role': 'assistant', 'content': log.answer[:500]})
            # 同时写回 Redis 以便后续使用
            for msg in messages:
                cache_service.append_conversation(session_id, msg['role'], msg['content'])

    if not messages:
        return jsonify({'code': 400, 'data': None, 'message': '没有可保存的对话'}), 400

    conv = Conversation.query.filter_by(session_id=session_id).first()
    if conv:
        conv.title = title or conv.title
        ConversationMessage.query.filter_by(conversation_id=conv.id).delete()
    else:
        conv = Conversation(
            user_id=user_id, session_id=session_id,
            title=title or (messages[0]['content'][:50] if messages else '新对话'),
        )
        db.session.add(conv)
        db.session.flush()

    for msg in messages:
        cm = ConversationMessage(conversation_id=conv.id, role=msg['role'], content=msg['content'])
        db.session.add(cm)
    conv.message_count = len(messages)
    db.session.commit()

    return jsonify({'code': 200, 'data': conv.to_dict(), 'message': '对话已保存'})


@qa_bp.route('/sessions', methods=['GET'])
@jwt_required()
def list_sessions():
    """获取当前用户的所有已保存对话"""
    user_id = int(get_jwt_identity())
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    query = Conversation.query.filter_by(user_id=user_id, is_active=True).order_by(
        Conversation.updated_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'code': 200,
        'data': {'list': [c.to_dict() for c in pagination.items], 'total': pagination.total, 'page': page, 'per_page': per_page},
        'message': '获取成功',
    })


@qa_bp.route('/sessions/<int:conv_id>', methods=['GET'])
@jwt_required()
def get_session_messages(conv_id: int):
    """获取已保存对话的完整消息"""
    user_id = int(get_jwt_identity())
    conv = Conversation.query.filter_by(id=conv_id, user_id=user_id).first()
    if not conv:
        return jsonify({'code': 404, 'data': None, 'message': '对话不存在'}), 404
    messages = [m.to_dict() for m in conv.messages.all()]
    return jsonify({'code': 200, 'data': {'conversation': conv.to_dict(), 'messages': messages}, 'message': '获取成功'})


@qa_bp.route('/sessions/<int:conv_id>', methods=['DELETE'])
@jwt_required()
def delete_session(conv_id: int):
    """删除已保存的对话"""
    user_id = int(get_jwt_identity())
    conv = Conversation.query.filter_by(id=conv_id, user_id=user_id).first()
    if not conv:
        return jsonify({'code': 404, 'data': None, 'message': '对话不存在'}), 404
    db.session.delete(conv)
    db.session.commit()
    return jsonify({'code': 200, 'data': None, 'message': '对话已删除'})


@qa_bp.route('/sessions/<int:conv_id>/restore', methods=['POST'])
@jwt_required()
def restore_session(conv_id: int):
    """恢复已保存的对话到 Redis（继续对话）"""
    user_id = int(get_jwt_identity())
    conv = Conversation.query.filter_by(id=conv_id, user_id=user_id).first()
    if not conv:
        return jsonify({'code': 404, 'data': None, 'message': '对话不存在'}), 404
    new_session_id = str(uuid.uuid4())
    cache_service.clear_conversation(new_session_id)
    for msg in conv.messages.all():
        cache_service.append_conversation(new_session_id, msg.role, msg.content)
    return jsonify({'code': 200, 'data': {'session_id': new_session_id, 'title': conv.title}, 'message': '对话已恢复'})
