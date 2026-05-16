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


class TestIngestionRoutes:
    def test_ingest_source_success(self, client, tmp_path):
        source = tmp_path / "api.txt"
        source.write_text("api document has refund policy", encoding="utf-8")
        response = client.post(
            "/ingest/source", json={"source": str(source), "file_type": "txt"}
        )
        assert response.status_code == 200
        assert response.json()["chunks_added"] >= 1

    def test_ingest_source_bad_type_returns_400(self, client):
        response = client.post(
            "/ingest/source", json={"source": "missing", "file_type": "bad"}
        )
        assert response.status_code == 400

    def test_auto_ingest_returns_summary(self, client):
        response = client.post("/ingest/auto")
        assert set(response.json()) == {"ingested", "skipped", "failed"}
