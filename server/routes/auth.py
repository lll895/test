# ============================================================================
# 企业知识库 RAG 问答系统 - 用户认证路由
# 功能：用户登录、注册、个人信息管理
# ============================================================================

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.user import User
from utils import db
from utils.logger import get_logger
import hashlib
import uuid
import os
from datetime import datetime

logger = get_logger(__name__)

# 创建认证蓝图
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def md5_encrypt(password: str) -> str:
    """
    MD5 加密函数
    Args:
        password: 明文密码
    Returns:
        MD5 加密后的密文
    """
    return hashlib.md5(password.encode('utf-8')).hexdigest()


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    用户登录接口
    ---
    请求体: {"username": "xxx", "password": "xxx"}
    返回: {"code": 200, "data": {"token": "...", "user": {...}}, "message": "登录成功"}
    """
    data = request.get_json()

    # 验证参数
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'code': 400, 'data': None, 'message': '用户名和密码不能为空'}), 400

    # 查找用户
    user = User.query.filter_by(username=username).first()

    if not user or user.password != md5_encrypt(password):
        return jsonify({'code': 401, 'data': None, 'message': '用户名或密码错误'}), 401

    if not user.status:
        return jsonify({'code': 403, 'data': None, 'message': '账号已被禁用，请联系管理员'}), 403

    # 更新最后登录时间
    user.last_login = datetime.now()
    db.session.commit()

    # 生成 JWT Token
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            'role': user.role,
            'username': user.username,
        }
    )

    return jsonify({
        'code': 200,
        'data': {
            'token': access_token,
            'user': user.to_dict(),
        },
        'message': '登录成功',
    })


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    用户注册接口
    ---
    请求体: {"username": "xxx", "password": "xxx", "real_name": "xxx", "email": "xxx"}
    返回: {"code": 200, "data": null, "message": "注册成功"}
    """
    data = request.get_json()

    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    real_name = data.get('real_name', '').strip()
    email = data.get('email', '').strip()

    # 参数校验
    if not username or not password:
        return jsonify({'code': 400, 'data': None, 'message': '用户名和密码不能为空'}), 400
    if len(username) < 3 or len(username) > 50:
        return jsonify({'code': 400, 'data': None, 'message': '用户名长度需在3-50个字符之间'}), 400
    if len(password) < 6:
        return jsonify({'code': 400, 'data': None, 'message': '密码长度不能少于6位'}), 400

    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({'code': 409, 'data': None, 'message': '用户名已存在'}), 409

    # 创建用户（默认角色为普通用户）
    user = User(
        username=username,
        password=md5_encrypt(password),
        real_name=real_name or username,
        email=email,
        role='user',
        status=True,
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({'code': 200, 'data': None, 'message': '注册成功'})


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    获取当前登录用户的个人信息
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user:
        return jsonify({'code': 404, 'data': None, 'message': '用户不存在'}), 404

    return jsonify({'code': 200, 'data': user.to_dict(), 'message': '获取成功'})


# ==================== 忘记密码 / 重置密码 ====================

_RESET_TOKEN_TTL = 1800  # 30 分钟


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    忘记密码 - 生成重置令牌（使用独立表，不影响 User 模型）
    请求体: {"username": "xxx", "email": "xxx"}
    """
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()

    if not username and not email:
        return jsonify({'code': 400, 'data': None, 'message': '请输入用户名或邮箱'}), 400

    # 查找用户
    query = User.query
    if username:
        query = query.filter_by(username=username)
    if email:
        query = query.filter(User.email == email)

    user = query.first()
    if not user:
        logger.info(f"密码重置请求: 用户不存在 username={username}, email={email}")
        return jsonify({'code': 200, 'data': None,
                        'message': '如果该账号存在，重置链接将通过邮箱发送'})

    # 创建重置令牌（使用独立表，自动使旧令牌失效）
    from models.password_reset import PasswordResetToken
    reset_token = PasswordResetToken.create_for_user(
        user_id=user.id,
        ttl_seconds=_RESET_TOKEN_TTL,
    )

    logger.info(f"密码重置令牌已生成: user={user.username}, expires_in={_RESET_TOKEN_TTL}s")

    # 开发/演示环境：直接返回令牌
    from config import Config
    env = getattr(Config, 'FLASK_ENV', 'development') or 'development'
    env = os.environ.get('FLASK_ENV', env)
    if env in ('development', 'testing'):
        return jsonify({
            'code': 200,
            'data': {
                'reset_token': reset_token.token,
                'expires_in': _RESET_TOKEN_TTL,
            },
            'message': '重置令牌已生成（开发模式）'
        })

    return jsonify({'code': 200, 'data': None,
                    'message': '如果该账号存在，重置链接将通过邮箱发送'})


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    使用重置令牌设置新密码
    请求体: {"token": "xxx", "new_password": "xxx"}
    """
    data = request.get_json()
    token_str = data.get('token', '').strip()
    new_password = data.get('new_password', '').strip()

    if not token_str or not new_password:
        return jsonify({'code': 400, 'data': None, 'message': '参数不完整'}), 400

    if len(new_password) < 6:
        return jsonify({'code': 400, 'data': None, 'message': '密码长度不能少于6位'}), 400

    # 验证令牌并消耗
    from models.password_reset import PasswordResetToken
    token_record = PasswordResetToken.verify_and_consume(token_str)

    if not token_record:
        return jsonify({'code': 400, 'data': None, 'message': '令牌无效或已过期，请重新申请'}), 400

    # 更新密码
    user = token_record.user
    user.password = md5_encrypt(new_password)
    db.session.commit()

    logger.info(f"密码重置成功: user={user.username}")
    return jsonify({'code': 200, 'data': None, 'message': '密码重置成功，请使用新密码登录'})


# ==================== 个人资料管理 ====================


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    更新个人资料
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user:
        return jsonify({'code': 404, 'data': None, 'message': '用户不存在'}), 404

    data = request.get_json()
    if 'real_name' in data:
        user.real_name = data['real_name']
    if 'email' in data:
        user.email = data['email']

    # 修改密码（需要原密码验证）
    if 'new_password' in data and 'old_password' in data:
        if user.password != md5_encrypt(data['old_password']):
            return jsonify({'code': 400, 'data': None, 'message': '原密码错误'}), 400
        user.password = md5_encrypt(data['new_password'])

    db.session.commit()

    return jsonify({'code': 200, 'data': user.to_dict(), 'message': '更新成功'})
