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


class TestIndexRoutes:
    def test_index_status(self, client, tmp_path):
        source = tmp_path / "idx.txt"
        source.write_text("index content alpha beta", encoding="utf-8")
        client.post("/ingest/source", json={"source": str(source), "file_type": "txt"})
        response = client.get("/index/status")
        assert response.json()["total_chunks"] >= 1

    def test_clear_index(self, client):
        assert client.delete("/index").json() == {"cleared": True}

    def test_remove_source_not_found_returns_404(self, client):
        response = client.delete("/index/source/nonexistent")
        assert response.status_code == 404

    def test_remove_source_found(self, client, tmp_path):
        source = tmp_path / "removable.txt"
        source.write_text("content for removal test alpha beta", encoding="utf-8")
        client.post("/ingest/source", json={"source": str(source), "file_type": "txt"})
        details = client.get("/index/status").json()["source_details"]
        sid = details[0]["source_id"]
        response = client.delete(f"/index/source/{sid}")
        assert response.json()["removed"] is True


# ── rag ──────────────────────────────────────────────────────────────────────
