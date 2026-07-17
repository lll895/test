"""
Tests for health check endpoints
=================================
Covers:
  - GET /api/health/live  -- always returns ok
  - GET /api/health/ready -- database-dependent status
  - GET /api/health       -- full dependency check
"""

import pytest


class TestLiveness:
    """GET /api/health/live"""

    URL = '/api/health/live'

    def test_live_returns_ok(self, client):
        """Liveness probe always returns status 'ok'."""
        resp = client.get(self.URL)
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['status'] == 'ok'

    def test_live_has_timestamp(self, client):
        """Liveness response includes an ISO timestamp."""
        resp = client.get(self.URL)
        data = resp.get_json()
        assert 'timestamp' in data
        assert data['timestamp'] is not None

    def test_live_returns_json(self, client):
        """Liveness response content type is JSON."""
        resp = client.get(self.URL)
        assert resp.content_type == 'application/json'


class TestReadiness:
    """GET /api/health/ready"""

    URL = '/api/health/ready'

    def test_ready_returns_ok_with_db(self, client):
        """Readiness probe returns ok when the database is reachable."""
        resp = client.get(self.URL)
        data = resp.get_json()
        assert resp.status_code == 200
        assert data['status'] == 'ok'
        assert 'database' in data['checks']

    def test_ready_includes_db_check(self, client):
        """Readiness response contains a database check result."""
        resp = client.get(self.URL)
        data = resp.get_json()
        assert data['checks']['database']['status'] == 'ok'

    def test_ready_has_timestamp(self, client):
        """Readiness response includes an ISO timestamp."""
        resp = client.get(self.URL)
        assert 'timestamp' in resp.get_json()


class TestHealth:
    """GET /api/health"""

    URL = '/api/health'

    def test_health_returns_overall_status(self, client):
        """Full health check returns an overall status."""
        resp = client.get(self.URL)
        data = resp.get_json()
        assert 'status' in data

    def test_health_includes_all_checks(self, client):
        """Full health check reports on database, redis, vector_store, llm."""
        resp = client.get(self.URL)
        data = resp.get_json()
        assert 'checks' in data
        checks = data['checks']
        # Because cache_service is mocked with is_connected=False, redis
        # will show as 'degraded'.  Vector store and LLM are also mocked.
        assert 'database' in checks
        assert 'redis' in checks
        assert 'vector_store' in checks
        assert 'llm' in checks

    def test_health_database_ok(self, client):
        """Database check is ok when SQLite is connected."""
        resp = client.get(self.URL)
        assert resp.get_json()['checks']['database']['status'] == 'ok'

    def test_health_redis_degraded(self, client):
        """Redis check is 'degraded' because cache_service is mocked offline."""
        resp = client.get(self.URL)
        status = resp.get_json()['checks']['redis']['status']
        # Either degraded (mock is_connected=False) or error
        assert status in ('degraded', 'error')

    def test_health_includes_summary(self, client):
        """Full health check includes summary counts."""
        resp = client.get(self.URL)
        data = resp.get_json()
        assert 'summary' in data
        assert 'total' in data['summary']
        assert 'ok' in data['summary']
        assert 'error' in data['summary']

    def test_health_summary_counts(self, client):
        """Summary counts are non-negative integers."""
        resp = client.get(self.URL)
        s = resp.get_json()['summary']
        assert s['total'] == 4
        assert isinstance(s['ok'], int)
        assert isinstance(s['error'], int)
