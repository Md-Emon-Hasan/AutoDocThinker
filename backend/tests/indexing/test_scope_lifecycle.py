"""Tests for scope lifecycle: DELETE /index/scope/{scope} and status counts."""

from fastapi.testclient import TestClient

from app.main import app

ADMIN_TOKEN_HEADER = {"X-Admin-Token": "test-admin-token-for-pytest"}


class TestScopeLifecycle:
    def test_delete_scope_clears_both_indices(self):
        client = TestClient(app)
        client.post(
            "/ingest/text", json={"text": "to be deleted alpha", "scope": "session:z"}
        )
        response = client.delete("/index/scope/session:z", headers=ADMIN_TOKEN_HEADER)
        assert response.status_code == 200
        body = response.json()
        assert body["removed"] is True
        assert body["bm25_chunks_removed"] >= 1
        assert body["dense_chunks_removed"] >= 1

    def test_delete_unknown_scope_returns_404(self):
        client = TestClient(app)
        response = client.delete(
            "/index/scope/session:never-existed", headers=ADMIN_TOKEN_HEADER
        )
        assert response.status_code == 404

    def test_delete_scope_requires_admin_token(self):
        client = TestClient(app)
        response = client.delete("/index/scope/session:z")
        assert response.status_code == 401

    def test_status_reports_per_scope_per_index_type(self):
        client = TestClient(app)
        client.post(
            "/ingest/text", json={"text": "scope status alpha", "scope": "session:s1"}
        )
        response = client.get("/index/status")
        body = response.json()
        assert "scope_counts" in body
        assert "dense" in body["scope_counts"]
        assert "bm25" in body["scope_counts"]
        assert body["scope_counts"]["bm25"].get("session:s1", 0) >= 1
        assert "index_version" in body

    def test_deleting_source_cascades_to_dense_index(self, tmp_path):
        client = TestClient(app)
        source = tmp_path / "cascade.txt"
        source.write_text("cascade delete content alpha", encoding="utf-8")
        client.post("/ingest/source", json={"source": str(source), "file_type": "txt"})
        details = client.get("/index/status").json()["source_details"]
        sid = details[0]["source_id"]
        response = client.delete(f"/index/source/{sid}", headers=ADMIN_TOKEN_HEADER)
        assert response.json()["removed"] is True
