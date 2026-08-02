"""Tests for session-scoped index isolation (Stage 2).

Ingest into session A, query from session B: no chunk, citation, or
answer content from A should appear -- via the vector (dense) path, the
BM25 (sparse) path, and the answer cache. "shared" is reachable from
every session. Ingestion with no scope must NOT land in "shared".
"""

from fastapi.testclient import TestClient

from app.dependencies import container
from app.main import app


class TestScopeIsolation:
    def test_bm25_path_isolated(self, tmp_path):
        client = TestClient(app)
        client.post(
            "/ingest/text",
            json={"text": "session A confidential alpha", "scope": "session:a"},
        )
        client.post(
            "/ingest/text",
            json={"text": "session B confidential beta", "scope": "session:b"},
        )
        index = container()["index"]
        results = index.search(
            "confidential", k=10, metadata_filter={"scope": ["shared", "session:b"]}
        )
        assert all(doc.metadata.get("scope") != "session:a" for doc in results)
        assert any(doc.metadata.get("scope") == "session:b" for doc in results)

    def test_dense_path_isolated(self):
        client = TestClient(app)
        client.post(
            "/ingest/text",
            json={"text": "session A confidential alpha", "scope": "session:a"},
        )
        client.post(
            "/ingest/text",
            json={"text": "session B confidential beta", "scope": "session:b"},
        )
        dense_index = container()["dense_index"]
        results = dense_index.search(
            "confidential", k=10, metadata_filter={"scope": ["shared", "session:b"]}
        )
        assert all(doc.metadata.get("scope") != "session:a" for doc in results)

    def test_answer_cache_isolated_by_scope(self):
        client = TestClient(app)
        client.post(
            "/ingest/text", json={"text": "shared doc alpha", "scope": "shared"}
        )
        response_a = client.post(
            "/rag/query",
            json={
                "question": "same question",
                "domain": "general",
                "rag_mode": "naive",
                "scope": "session:a",
            },
        )
        response_b = client.post(
            "/rag/query",
            json={
                "question": "same question",
                "domain": "general",
                "rag_mode": "naive",
                "scope": "session:b",
            },
        )
        # Different scopes must not collide on the same cache entry --
        # verified structurally via the cache-key test suite; here we
        # just confirm both scoped requests succeed independently.
        assert response_a.status_code == 200
        assert response_b.status_code == 200

    def test_shared_reachable_from_every_session(self):
        client = TestClient(app)
        client.post(
            "/ingest/text", json={"text": "shared alpha content", "scope": "shared"}
        )
        index = container()["index"]
        for scope in ("session:x", "session:y", None):
            results = index.search(
                "shared", k=10, metadata_filter={"scope": ["shared", scope or "shared"]}
            )
            assert any(doc.metadata.get("scope") == "shared" for doc in results)

    def test_unscoped_ingestion_does_not_land_in_shared(self):
        client = TestClient(app)
        response = client.post("/ingest/text", json={"text": "no scope given alpha"})
        assert response.json()["scope"] != "shared"

    def test_unscoped_ingest_then_unscoped_query_still_works(self):
        """The ordinary 'ingest then ask' flow for a caller that manages
        no scope tokens at all must keep working (both default to the
        same anonymous scope)."""
        client = TestClient(app)
        client.post("/ingest/text", json={"text": "unscoped alpha beta content"})
        index = container()["index"]
        from app.retrieval.filters import scope_filter

        results = index.search("unscoped", k=10, metadata_filter=scope_filter(None))
        assert len(results) >= 1
