"""
Pytest conftest.py - Test configuration, fixtures, and mocks
=============================================================
Provides:
  - Flask test app with SQLite in-memory database
  - Mocked cache_service, vector_service, and langchain_ollama
  - Test client fixture
  - Database setup/teardown fixture
  - Auth helper fixture
"""

import os
import sys
from unittest.mock import MagicMock

# ============================================================================
# Module-level setup -- runs before ANY test or fixture is imported
# This is necessary because importing the app module triggers:
#   - Redis connection (cache_service)
#   - Chroma/Ollama initialization (vector_service)
#   - MySQL database initialization / table creation
# ============================================================================

# ---- Ensure the server directory is on sys.path ----
SERVER_DIR = os.path.join(os.path.dirname(__file__), '..')
if SERVER_DIR not in sys.path:
    sys.path.insert(0, SERVER_DIR)

# ---- Test environment (minimal, to preserve Config defaults for testing) ----
os.environ.setdefault('FLASK_ENV', 'testing')

# ---- Patch MySQL JSON type for SQLite compatibility ----
# The QaLog, Conversation, and ConversationMessage models use MySQL's JSON
# column type, which is not supported by SQLite.  We replace it with Text
# so that table creation works in our in-memory database.
import sqlalchemy as sa
# Explicitly import the mysql dialect so the attribute tree is populated
import sqlalchemy.dialects.mysql as _mysql_dialect
sa.dialects.mysql.JSON = sa.Text

# ---- Mock langchain_ollama (avoids needing a real Ollama server) ----
# llm_service.py imports ChatOllama at module level.  Without this mock
# the import would fail when the Ollama server is not running.
mock_chat_ollama_cls = MagicMock(name='ChatOllama')
langchain_ollama_module = MagicMock(name='langchain_ollama')
langchain_ollama_module.ChatOllama = mock_chat_ollama_cls
sys.modules['langchain_ollama'] = langchain_ollama_module

# ---- Mock Redis connection in cache_service ----
mock_cache = MagicMock(name='cache_service')
mock_cache.is_connected = False
mock_cache.get_qa_cache.return_value = None
mock_cache.set_qa_cache.return_value = None
mock_cache.get_vector_cache.return_value = None
mock_cache.set_vector_cache.return_value = None
mock_cache.get_conversation_context.return_value = []
mock_cache.append_conversation.return_value = None
mock_cache.clear_conversation.return_value = None
mock_cache.delete_pattern.return_value = 0
mock_cache.invalidate_qa_cache.return_value = None
mock_cache.invalidate_vector_cache.return_value = None

cache_module = MagicMock(name='services.cache_service')
cache_module.cache_service = mock_cache
sys.modules['services.cache_service'] = cache_module

# ---- Mock vector_service (avoids needing Chroma + OllamaEmbeddings) ----
mock_vector = MagicMock(name='vector_service')
mock_vector.similarity_search.return_value = []
mock_vector.get_document_count.return_value = 0
mock_vector.add_document.return_value = []
mock_vector.split_document.return_value = []

vector_module = MagicMock(name='services.vector_service')
vector_module.vector_service = mock_vector
sys.modules['services.vector_service'] = vector_module

# ---- Override Config to use SQLite ----
import config as _config_mod
# Save the original value so test_config can check it
_original_db_uri = _config_mod.Config.SQLALCHEMY_DATABASE_URI
_config_mod.Config.SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
_config_mod.Config.SQLALCHEMY_TRACK_MODIFICATIONS = False

# ---- Now it is safe to import the app module ----
from app import app as _flask_app

# ---- Drop tables created by init_db during import (we re-create per test) ----
with _flask_app.app_context():
    from utils import db as _db
    _db.drop_all()

# ============================================================================
# Public fixture API
# ============================================================================

import pytest


@pytest.fixture(scope='session')
def app():
    """Return the Flask application configured for testing."""
    return _flask_app


@pytest.fixture(scope='session')
def client(app):
    """Return a Flask test client bound to the app."""
    return app.test_client()


@pytest.fixture(autouse=True)
def db(app):
    """
    Set up all database tables before each test and tear them down afterwards.

    Because this fixture is *autouse* it runs for every test function without
    the test having to request it explicitly.
    """
    from utils import db as _db
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def auth_headers(app, client):
    """
    Register + login a test user and return the Authorization header dict.

    Usage::

        def test_something(auth_headers):
            response = client.get('/api/...', headers=auth_headers)
    """
    client.post('/api/auth/register', json={
        'username': 'testuser',
        'password': 'test123456',
        'real_name': 'Test User',
    })
    resp = client.post('/api/auth/login', json={
        'username': 'testuser',
        'password': 'test123456',
    })
    data = resp.get_json()
    token = data['data']['token']
    return {'Authorization': f'Bearer {token}'}


# Convenience references so test files can import these mocks directly.
# This allows test files to configure mock return values per test.
@pytest.fixture(autouse=True)
def _reset_mocks():
    """Reset all mocks before each test so test isolation is maintained."""
    # Full reset clears return_value, side_effect, and call history
    mock_cache.reset_mock()
    mock_vector.reset_mock()

    # Re-apply default return values after the reset
    mock_cache.is_connected = False
    mock_cache.get_qa_cache.return_value = None
    mock_cache.set_qa_cache.return_value = None
    mock_cache.get_vector_cache.return_value = None
    mock_cache.set_vector_cache.return_value = None
    mock_cache.get_conversation_context.return_value = []
    mock_cache.append_conversation.return_value = None
    mock_cache.clear_conversation.return_value = None
    mock_cache.delete_pattern.return_value = 0

    mock_vector.similarity_search.return_value = []
    mock_vector.get_document_count.return_value = 0
    mock_vector.add_document.return_value = []
    mock_vector.split_document.return_value = []


# Export mocks so test modules can access them
@pytest.fixture
def mock_cache_service():
    """Return the shared cache_service mock for configuring per-test behaviour."""
    return mock_cache


@pytest.fixture
def mock_vector_service():
    """Return the shared vector_service mock for configuring per-test behaviour."""
    return mock_vector


@pytest.fixture
def original_db_uri():
    """Return the original SQLALCHEMY_DATABASE_URI before conftest overrode it."""
    return _original_db_uri
