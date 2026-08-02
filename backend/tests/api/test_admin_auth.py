"""Every admin/destructive endpoint rejects missing/wrong token, accepts
the right one, and refuses outright when ADMIN_TOKEN is unset."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

ADMIN_TOKEN_HEADER = {"X-Admin-Token": "test-admin-token-for-pytest"}
WRONG_TOKEN_HEADER = {"X-Admin-Token": "wrong-token"}

_PROTECTED_ENDPOINTS = [
    ("DELETE", "/index"),
    ("DELETE", "/index/source/nonexistent"),
    ("DELETE", "/index/scope/session:nonexistent"),
    ("GET", "/admin/summary"),
    ("GET", "/admin/cache/stats"),
    ("POST", "/admin/cache/clear"),
    ("GET", "/governance/audit"),
    ("GET", "/hitl/pending"),
]


@pytest.fixture()
def client():
    return TestClient(app)


class TestAdminAuth:
    @pytest.mark.parametrize("method,path", _PROTECTED_ENDPOINTS)
    def test_rejects_missing_token(self, client, method, path):
        response = client.request(method, path)
        assert response.status_code == 401

    @pytest.mark.parametrize("method,path", _PROTECTED_ENDPOINTS)
    def test_rejects_wrong_token(self, client, method, path):
        response = client.request(method, path, headers=WRONG_TOKEN_HEADER)
        assert response.status_code == 401

    @pytest.mark.parametrize("method,path", _PROTECTED_ENDPOINTS)
    def test_accepts_correct_token(self, client, method, path):
        response = client.request(method, path, headers=ADMIN_TOKEN_HEADER)
        assert response.status_code != 401
        assert response.status_code != 503

    @pytest.mark.parametrize("method,path", _PROTECTED_ENDPOINTS)
    def test_refuses_when_token_unset(self, client, method, path, monkeypatch):
        monkeypatch.delenv("ADMIN_TOKEN", raising=False)
        response = client.request(method, path, headers=ADMIN_TOKEN_HEADER)
        assert response.status_code == 503
