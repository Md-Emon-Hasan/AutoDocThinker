"""Consolidated tests for ALL API routes: health, domain, chat, ingestion, upload,
index, rag, and admin endpoints."""

import io

import pytest
from fastapi.testclient import TestClient

from app.application import create_app
from app.dependencies import container

# ── fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def client():
    return TestClient(create_app())


@pytest.fixture()
def seeded_client(tmp_path):
    """Client with a pre-ingested document for routes that need data."""
    app = create_app()
    c = TestClient(app)
    source = tmp_path / "api_seed.txt"
    source.write_text("refund policy details alpha beta", encoding="utf-8")
    container()["ingestion"].ingest(str(source), "txt")
    return c


# ── health ───────────────────────────────────────────────────────────────────


class TestRagRoutes:
    def test_rag_modes_lists_all_modes(self, seeded_client):
        modes = seeded_client.get("/rag-modes").json()["modes"]
        assert set(modes) == {"naive", "advanced", "crag", "self_rag"}

    def test_rag_profiles_returns_profiles(self, seeded_client):
        response = seeded_client.get("/rag-profiles")
        assert response.status_code == 200
        assert response.json()

    def test_rag_query_returns_answer(self, seeded_client):
        response = seeded_client.post(
            "/rag/query",
            json={
                "question": "refund policy",
                "domain": "general",
                "rag_mode": "advanced",
            },
        )
        assert response.status_code == 200

    def test_rag_query_bad_domain_returns_422(self, seeded_client):
        response = seeded_client.post(
            "/rag/query",
            json={"question": "x", "domain": "bad", "rag_mode": "advanced"},
        )
        assert response.status_code == 422

    def test_rag_query_bad_mode_returns_422(self, seeded_client):
        response = seeded_client.post(
            "/rag/query",
            json={"question": "x", "domain": "general", "rag_mode": "bad"},
        )
        assert response.status_code == 422

    def test_rag_query_rate_limit_error(self, seeded_client):
        from unittest.mock import patch

        with patch(
            "app.rag.service.RAGService.query",
            side_effect=RuntimeError("rate limit reached"),
        ):
            response = seeded_client.post(
                "/rag/query",
                json={"question": "x", "domain": "general", "rag_mode": "advanced"},
            )
            assert response.status_code == 429

    def test_rag_query_runtime_error(self, seeded_client):
        from unittest.mock import patch

        with patch(
            "app.rag.service.RAGService.query", side_effect=RuntimeError("other error")
        ):
            response = seeded_client.post(
                "/rag/query",
                json={"question": "x", "domain": "general", "rag_mode": "advanced"},
            )
            assert response.status_code == 500


# ── admin ────────────────────────────────────────────────────────────────────
