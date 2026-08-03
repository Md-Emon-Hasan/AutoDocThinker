"""Consolidated tests for ALL API routes: health, domain, chat, ingestion, upload,
index, rag, and admin endpoints."""

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


class TestIngestTextRoutes:
    def test_ingest_text_success(self, client):
        response = client.post(
            "/ingest/text",
            json={"text": "Some important knowledge base text", "title": "My Title"},
        )
        assert response.status_code == 200

    def test_ingest_text_empty_returns_400(self, client):
        response = client.post("/ingest/text", json={"text": "   ", "title": "x"})
        assert response.status_code == 400

    def test_ingest_text_default_title(self, client):
        response = client.post(
            "/ingest/text", json={"text": "Content without explicit title"}
        )
        assert response.status_code == 200

    def test_ingest_text_error(self, client):
        from unittest.mock import patch

        with patch(
            "app.ingestion.service.IngestionService.ingest",
            side_effect=RuntimeError("mock ingest text error"),
        ):
            response = client.post(
                "/ingest/text", json={"text": "Content without explicit title"}
            )
            assert response.status_code == 400


# ── index ────────────────────────────────────────────────────────────────────
