"""Tests for app/governance/audit.py::AuditLog."""

from fastapi.testclient import TestClient

from app.governance.audit import AuditLog
from app.main import app

ADMIN_TOKEN_HEADER = {"X-Admin-Token": "test-admin-token-for-pytest"}


class TestAuditLog:
    def test_record_and_list(self, tmp_path):
        log = AuditLog(tmp_path / "audit.sqlite3")
        log.record(
            "session:a", "prompt_injection", "blocked", reason="ignore all instructions"
        )
        result = log.list()
        assert result["total"] == 1
        assert result["items"][0]["rule"] == "prompt_injection"
        assert result["items"][0]["action"] == "blocked"

    def test_no_raw_pii_persisted(self, tmp_path):
        log = AuditLog(tmp_path / "audit.sqlite3")
        log.record("session:a", "pii_leakage", "blocked", reason="jane@example.com")
        result = log.list()
        item = result["items"][0]
        assert "jane@example.com" not in str(item)
        assert item["reason_hash"] is not None
        assert item["reason_hash"] != "jane@example.com"

    def test_pagination(self, tmp_path):
        log = AuditLog(tmp_path / "audit.sqlite3")
        for i in range(5):
            log.record("session:a", f"rule{i}", "blocked")
        page1 = log.list(limit=2, offset=0)
        page2 = log.list(limit=2, offset=2)
        assert len(page1["items"]) == 2
        assert len(page2["items"]) == 2
        assert page1["total"] == 5
        assert page1["items"] != page2["items"]

    def test_survives_reopen(self, tmp_path):
        db_path = tmp_path / "audit.sqlite3"
        AuditLog(db_path).record("session:a", "rule", "blocked")
        reopened = AuditLog(db_path)
        assert reopened.list()["total"] == 1


class TestAuditRouteRequiresAdminToken:
    def test_governance_audit_requires_token(self):
        client = TestClient(app)
        assert client.get("/governance/audit").status_code == 401

    def test_governance_audit_with_token(self):
        client = TestClient(app)
        response = client.get("/governance/audit", headers=ADMIN_TOKEN_HEADER)
        assert response.status_code == 200
        assert "items" in response.json()
