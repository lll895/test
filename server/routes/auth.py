# ============================================================================
# 企业知识库 RAG 问答系统 - 用户认证路由
# 功能：用户登录、注册、个人信息管理
# ============================================================================

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.user import User
from utils import db
import hashlib
from datetime import datetime

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
