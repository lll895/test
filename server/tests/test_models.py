"""
Tests for SQLAlchemy model serialization and permission methods
===============================================================
Covers:
  - User.to_dict()     -- password is never included
  - User.has_permission() -- admin / user role checks
  - Document.to_dict()  -- expected keys present
"""

import pytest
from datetime import datetime
from utils import db


class TestUserModel:
    """User model serialization and permissions."""

    def test_to_dict_excludes_password(self, app):
        """User.to_dict() must NOT include the password field."""
        from models.user import User
        with app.app_context():
            user = User(
                username='secretuser',
                password='should-not-leak',
                role='user',
                status=True,
            )
            db.session.add(user)
            db.session.commit()

            result = user.to_dict()
            assert 'password' not in result
            assert result['username'] == 'secretuser'
            assert result['role'] == 'user'

    def test_to_dict_includes_expected_keys(self, app):
        """User.to_dict() returns the correct set of keys."""
        from models.user import User
        with app.app_context():
            user = User(
                username='keycheck',
                password='ignored',
                role='admin',
                status=True,
            )
            db.session.add(user)
            db.session.commit()
            result = user.to_dict()

        expected_keys = {'id', 'username', 'real_name', 'email', 'role',
                         'status', 'avatar', 'last_login', 'created_at'}
        assert set(result.keys()) == expected_keys

    def test_admin_has_admin_permission(self, app):
        """A user with role='admin' passes has_permission('admin')."""
        from models.user import User
        with app.app_context():
            admin = User(username='admin1', password='x', role='admin', status=True)
            db.session.add(admin)
            db.session.commit()
            assert admin.has_permission('admin') is True

    def test_user_does_not_have_admin_permission(self, app):
        """A user with role='user' fails has_permission('admin')."""
        from models.user import User
        with app.app_context():
            regular = User(username='regular1', password='x', role='user', status=True)
            db.session.add(regular)
            db.session.commit()
            assert regular.has_permission('admin') is False

    def test_user_has_user_permission(self, app):
        """Any authenticated user passes has_permission('user')."""
        from models.user import User
        with app.app_context():
            user = User(username='anyuser', password='x', role='user', status=True)
            db.session.add(user)
            db.session.commit()
            assert user.has_permission('user') is True

    def test_admin_also_has_user_permission(self, app):
        """An admin also passes has_permission('user')."""
        from models.user import User
        with app.app_context():
            admin = User(username='admin2', password='x', role='admin', status=True)
            db.session.add(admin)
            db.session.commit()
            assert admin.has_permission('user') is True

    def test_to_dict_datetime_format(self, app):
        """created_at and last_login are ISO-format strings or None."""
        from models.user import User
        from datetime import datetime
        with app.app_context():
            user = User(
                username='timecheck',
                password='x',
                role='user',
                status=True,
                last_login=datetime(2024, 6, 15, 10, 30, 0),
            )
            db.session.add(user)
            db.session.commit()
            result = user.to_dict()
            assert result['last_login'] == '2024-06-15T10:30:00'
            assert result['created_at'] is not None  # auto-set by default


class TestDocumentModel:
    """Document model serialization."""

    def test_to_dict_expected_keys(self, app):
        """Document.to_dict() returns the full set of serializable keys."""
        from models.user import User
        from models.document import Document, Category
        with app.app_context():
            uploader = User(username='uploader1', password='x', role='user', status=True)
            db.session.add(uploader)
            db.session.flush()

            cat = Category(name='Test Category')
            db.session.add(cat)
            db.session.flush()

            doc = Document(
                title='Test Doc',
                file_name='test.txt',
                file_path='/uploads/test.txt',
                file_size=1024,
                file_type='txt',
                summary='A test document',
                category_id=cat.id,
                uploaded_by=uploader.id,
                status='ready',
                chunk_count=5,
            )
            db.session.add(doc)
            db.session.commit()

            result = doc.to_dict()

        expected_keys = {
            'id', 'title', 'file_name', 'file_path', 'file_size', 'file_type',
            'summary', 'content_text', 'category_id', 'category_name',
            'uploader', 'status', 'chunk_count', 'error_message',
            'version', 'version_group_id', 'change_note',
            'created_at', 'updated_at',
        }
        assert set(result.keys()) == expected_keys
        assert result['title'] == 'Test Doc'
        assert result['status'] == 'ready'

    def test_to_dict_includes_uploader_name(self, app):
        """to_dict() resolves uploader to real_name or username."""
        from models.user import User
        from models.document import Document
        with app.app_context():
            uploader = User(username='janedoe', password='x', role='user',
                            status=True, real_name='Jane Doe')
            db.session.add(uploader)
            db.session.flush()

            doc = Document(title='Doc2', file_name='a.txt', uploaded_by=uploader.id)
            db.session.add(doc)
            db.session.commit()

            result = doc.to_dict()
            assert result['uploader'] == 'Jane Doe'

    def test_to_dict_uploader_falls_back_to_username(self, app):
        """When real_name is None, uploader falls back to username."""
        from models.user import User
        from models.document import Document
        with app.app_context():
            uploader = User(username='norealname', password='x', role='user', status=True)
            db.session.add(uploader)
            db.session.flush()

            doc = Document(title='Doc3', file_name='b.txt', uploaded_by=uploader.id)
            db.session.add(doc)
            db.session.commit()

            result = doc.to_dict()
            assert result['uploader'] == 'norealname'

    def test_to_dict_includes_category_name(self, app):
        """to_dict() resolves category name."""
        from models.user import User
        from models.document import Document, Category
        with app.app_context():
            uploader = User(username='catcheck', password='x', role='user', status=True)
            db.session.add(uploader)
            db.session.flush()

            cat = Category(name='Technical Docs')
            db.session.add(cat)
            db.session.flush()

            doc = Document(title='Doc4', file_name='c.txt',
                           uploaded_by=uploader.id, category_id=cat.id)
            db.session.add(doc)
            db.session.commit()

            result = doc.to_dict()
            assert result['category_name'] == 'Technical Docs'
