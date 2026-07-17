"""
Tests for the Config class
===========================
Verifies default values and environment variable overrides.
"""

import os
import pytest


class TestConfigDefaults:
    """Verify that Config class provides sensible defaults."""

    def test_import_config(self):
        """Config can be imported and instantiated."""
        from config import Config
        # Access a few well-known attributes
        assert hasattr(Config, 'SECRET_KEY')
        assert hasattr(Config, 'SQLALCHEMY_DATABASE_URI')
        assert hasattr(Config, 'JWT_SECRET_KEY')

    def test_default_secret_key(self, monkeypatch):
        """SECRET_KEY has a default when no env var is set."""
        monkeypatch.delenv('SECRET_KEY', raising=False)
        import importlib
        import config
        importlib.reload(config)
        assert config.Config.SECRET_KEY == 'enterprise-oa-secret-key-2024'

    def test_default_jwt_secret(self, monkeypatch):
        """JWT_SECRET_KEY has a sensible default."""
        monkeypatch.delenv('JWT_SECRET_KEY', raising=False)
        import importlib
        import config
        importlib.reload(config)
        assert config.Config.JWT_SECRET_KEY == 'jwt-secret-key-enterprise-2024'

    def test_database_uri_default_is_mysql(self, original_db_uri):
        """SQLALCHEMY_DATABASE_URI defaults to mysql+pymysql:// when not overridden."""
        assert original_db_uri.startswith('mysql+pymysql://')

    def test_default_port_and_host(self):
        """DB_HOST and DB_PORT have sensible defaults."""
        from config import Config
        assert Config.DB_HOST == '127.0.0.1'
        assert Config.DB_PORT == 3306

    def test_jwt_expiry(self):
        """JWT_ACCESS_TOKEN_EXPIRES defaults to 86400 (24 h)."""
        from config import Config
        assert Config.JWT_ACCESS_TOKEN_EXPIRES == 86400

    def test_ollama_defaults(self):
        """Ollama-related settings have reasonable defaults."""
        from config import Config
        assert Config.OLLAMA_BASE_URL == 'http://127.0.0.1:11434'
        assert Config.LLM_MODEL == 'qwen2.5:3b'
        assert Config.EMBEDDING_MODEL is not None

    def test_rag_params(self):
        """RAG parameter defaults."""
        from config import Config
        assert Config.CHUNK_SIZE == 500
        assert Config.CHUNK_OVERLAP == 50
        assert Config.RETRIEVAL_K == 5

    def test_redis_defaults(self):
        """Redis host/port defaults."""
        from config import Config
        assert Config.REDIS_HOST == '127.0.0.1'
        assert Config.REDIS_PORT == 6379

    def test_log_defaults(self):
        """LOG_LEVEL defaults to INFO."""
        from config import Config
        assert Config.LOG_LEVEL == 'INFO'


class TestConfigEnvOverrides:
    """Verify that environment variables override Config defaults."""

    SECRET_KEY = 'my-custom-secret'
    DB_HOST_VAL = '10.0.0.1'
    DB_PORT_VAL = '3307'
    REDIS_HOST_VAL = '192.168.1.50'

    @pytest.fixture(autouse=True)
    def _set_env(self, monkeypatch):
        monkeypatch.setenv('SECRET_KEY', self.SECRET_KEY)
        monkeypatch.setenv('DB_HOST', self.DB_HOST_VAL)
        monkeypatch.setenv('DB_PORT', self.DB_PORT_VAL)
        monkeypatch.setenv('REDIS_HOST', self.REDIS_HOST_VAL)
        monkeypatch.setenv('LOG_LEVEL', 'DEBUG')
        monkeypatch.setenv('LLM_MODEL', 'llama3:8b')

    def test_secret_key_override(self, monkeypatch):
        """SECRET_KEY picks up the environment variable."""
        import importlib
        import config
        importlib.reload(config)
        assert config.Config.SECRET_KEY == self.SECRET_KEY

    def test_db_host_override(self, monkeypatch):
        """DB_HOST is overridden by environment variable."""
        import importlib
        import config
        importlib.reload(config)
        assert config.Config.DB_HOST == self.DB_HOST_VAL

    def test_db_port_override(self, monkeypatch):
        """DB_PORT is overridden by environment variable."""
        import importlib
        import config
        importlib.reload(config)
        assert config.Config.DB_PORT == int(self.DB_PORT_VAL)

    def test_redis_host_override(self, monkeypatch):
        """REDIS_HOST is overridden by environment variable."""
        import importlib
        import config
        importlib.reload(config)
        assert config.Config.REDIS_HOST == self.REDIS_HOST_VAL

    def test_log_level_override(self, monkeypatch):
        """LOG_LEVEL is overridden by environment variable."""
        import importlib
        import config
        importlib.reload(config)
        assert config.Config.LOG_LEVEL == 'DEBUG'

    def test_llm_model_override(self, monkeypatch):
        """LLM_MODEL is overridden by environment variable."""
        import importlib
        import config
        importlib.reload(config)
        assert config.Config.LLM_MODEL == 'llama3:8b'

    def test_database_uri_reflects_overrides(self, monkeypatch):
        """SQLALCHEMY_DATABASE_URI incorporates host/port/user/password/name
        from the environment."""
        import importlib
        import config
        importlib.reload(config)
        uri = config.Config.SQLALCHEMY_DATABASE_URI
        assert self.DB_HOST_VAL in uri
        assert self.DB_PORT_VAL in uri


class TestConfigSubclasses:
    """Verify that DevelopmentConfig and ProductionConfig inherit correctly."""

    def test_development_config_debug_true(self):
        from config import DevelopmentConfig
        assert DevelopmentConfig.DEBUG is True

    def test_production_config_debug_false(self):
        from config import ProductionConfig
        assert ProductionConfig.DEBUG is False

    def test_config_map(self):
        from config import config_map
        assert 'development' in config_map
        assert 'production' in config_map

    def test_config_map_types(self):
        from config import config_map
        from config import DevelopmentConfig, ProductionConfig
        assert config_map['development'] is DevelopmentConfig
        assert config_map['production'] is ProductionConfig
