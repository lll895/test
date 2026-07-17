"""
Tests for the auth API endpoints
=================================
Covers:
  - POST /api/auth/register (success, duplicate, missing fields)
  - POST /api/auth/login    (success, wrong password, disabled user)
"""

import pytest
from utils import db


class TestRegister:
    """POST /api/auth/register"""

    REGISTER_URL = '/api/auth/register'

    def test_register_success(self, client):
        """A valid registration returns 200 and success message."""
        resp = client.post(self.REGISTER_URL, json={
            'username': 'newuser',
            'password': 'pass123456',
            'real_name': 'New User',
            'email': 'new@example.com',
        })
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['code'] == 200
        assert data['message'] == '注册成功'

    def test_register_duplicate_username(self, client):
        """Registering the same username twice returns 409."""
        # Create user once
        client.post(self.REGISTER_URL, json={
            'username': 'dupe',
            'password': 'pass123456',
        })
        # Try again
        resp = client.post(self.REGISTER_URL, json={
            'username': 'dupe',
            'password': 'anotherpass1',
        })
        data = resp.get_json()
        assert resp.status_code == 409
        assert data['code'] == 409
        assert '已存在' in data['message']

    def test_register_missing_username(self, client):
        """Missing username returns 400."""
        resp = client.post(self.REGISTER_URL, json={
            'password': 'pass123456',
        })
        data = resp.get_json()
        assert resp.status_code == 400
        assert data['code'] == 400
        assert '用户名' in data['message'] or '不能为空' in data['message']

    def test_register_missing_password(self, client):
        """Missing password returns 400."""
        resp = client.post(self.REGISTER_URL, json={
            'username': 'nopassuser',
        })
        data = resp.get_json()
        assert resp.status_code == 400
        assert data['code'] == 400
        assert '密码' in data['message'] or '不能为空' in data['message']

    def test_register_username_too_short(self, client):
        """Username shorter than 3 characters returns 400."""
        resp = client.post(self.REGISTER_URL, json={
            'username': 'ab',
            'password': 'pass123456',
        })
        assert resp.status_code == 400

    def test_register_password_too_short(self, client):
        """Password shorter than 6 characters returns 400."""
        resp = client.post(self.REGISTER_URL, json={
            'username': 'validuser',
            'password': '12345',
        })
        assert resp.status_code == 400

    def test_register_sets_role_to_user(self, client):
        """A newly registered user has the 'user' role."""
        client.post(self.REGISTER_URL, json={
            'username': 'rolecheck',
            'password': 'pass123456',
        })
        from models.user import User
        user = User.query.filter_by(username='rolecheck').first()
        assert user is not None
        assert user.role == 'user'

    def test_register_sets_status_active(self, client):
        """A newly registered user is active (status=True)."""
        client.post(self.REGISTER_URL, json={
            'username': 'statuscheck',
            'password': 'pass123456',
        })
        from models.user import User
        user = User.query.filter_by(username='statuscheck').first()
        assert user is not None
        assert user.status is True


class TestLogin:
    """POST /api/auth/login"""

    LOGIN_URL = '/api/auth/login'
    REGISTER_URL = '/api/auth/register'

    USERNAME = 'loginuser'
    PASSWORD = 'loginpass123'

    @pytest.fixture(autouse=True)
    def _setup_user(self, client):
        """Register a test user before each login test."""
        client.post(self.REGISTER_URL, json={
            'username': self.USERNAME,
            'password': self.PASSWORD,
            'real_name': 'Login User',
        })

    def test_login_success(self, client):
        """Valid credentials return 200 with a JWT token and user info."""
        resp = client.post(self.LOGIN_URL, json={
            'username': self.USERNAME,
            'password': self.PASSWORD,
        })
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['code'] == 200
        assert data['message'] == '登录成功'
        assert 'token' in data['data']
        assert 'user' in data['data']
        assert data['data']['user']['username'] == self.USERNAME

    def test_login_returns_token(self, client):
        """Login response contains a non-empty JWT token."""
        resp = client.post(self.LOGIN_URL, json={
            'username': self.USERNAME,
            'password': self.PASSWORD,
        })
        token = resp.get_json()['data']['token']
        assert token is not None
        assert len(token) > 20

    def test_login_user_info_no_password(self, client):
        """User info in login response does NOT include the password field."""
        resp = client.post(self.LOGIN_URL, json={
            'username': self.USERNAME,
            'password': self.PASSWORD,
        })
        user_data = resp.get_json()['data']['user']
        assert 'password' not in user_data

    def test_login_wrong_password(self, client):
        """Wrong password returns 401."""
        resp = client.post(self.LOGIN_URL, json={
            'username': self.USERNAME,
            'password': 'wrongpassword99',
        })
        data = resp.get_json()
        assert resp.status_code == 401
        assert data['code'] == 401
        assert '错误' in data['message'] or '不正确' in data['message']

    def test_login_nonexistent_user(self, client):
        """Non-existent username returns 401."""
        resp = client.post(self.LOGIN_URL, json={
            'username': 'nobody',
            'password': 'somepassword',
        })
        assert resp.status_code == 401

    def test_login_disabled_user(self, client, app):
        """A disabled (status=False) user cannot log in and gets 403."""
        from models.user import User
        with app.app_context():
            user = User.query.filter_by(username=self.USERNAME).first()
            user.status = False
            db.session.commit()

        resp = client.post(self.LOGIN_URL, json={
            'username': self.USERNAME,
            'password': self.PASSWORD,
        })
        data = resp.get_json()
        assert resp.status_code == 403
        assert data['code'] == 403
        assert '禁用' in data['message']

    def test_login_missing_fields(self, client):
        """Missing username or password returns 400."""
        resp = client.post(self.LOGIN_URL, json={
            'username': '',
            'password': '',
        })
        assert resp.status_code == 400


class TestProfile:
    """GET /api/auth/profile (protected endpoint)"""

    REGISTER_URL = '/api/auth/register'
    LOGIN_URL = '/api/auth/login'
    PROFILE_URL = '/api/auth/profile'

    @pytest.fixture(autouse=True)
    def _setup(self, client):
        client.post(self.REGISTER_URL, json={
            'username': 'profileuser',
            'password': 'profilepass1',
        })
        resp = client.post(self.LOGIN_URL, json={
            'username': 'profileuser',
            'password': 'profilepass1',
        })
        self.token = resp.get_json()['data']['token']

    def _headers(self):
        return {'Authorization': f'Bearer {self.token}'}

    def test_get_profile_success(self, client):
        """Authenticated user can retrieve their profile."""
        resp = client.get(self.PROFILE_URL, headers=self._headers())
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['data']['username'] == 'profileuser'

    def test_get_profile_no_auth(self, client):
        """Request without token returns 401."""
        resp = client.get(self.PROFILE_URL)
        assert resp.status_code == 401

    def test_get_profile_excludes_password(self, client):
        """Profile response does not include password."""
        resp = client.get(self.PROFILE_URL, headers=self._headers())
        assert 'password' not in resp.get_json()['data']
