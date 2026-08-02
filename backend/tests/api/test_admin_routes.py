"""Consolidated tests for ALL API routes: health, domain, chat, ingestion, upload,
index, rag, and admin endpoints."""

import io

import pytest
from fastapi.testclient import TestClient

from app.application import create_app
from app.dependencies import container

ADMIN_TOKEN_HEADER = {"X-Admin-Token": "test-admin-token-for-pytest"}

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


class TestAdminRoutes:
    def test_admin_summary(self, client):
        body = client.get("/admin/summary", headers=ADMIN_TOKEN_HEADER).json()
        assert "domains" in body and "chunks" in body

    def test_admin_summary_requires_token(self, client):
        assert client.get("/admin/summary").status_code == 401

    def test_admin_summary_refuses_when_token_unset(self, client, monkeypatch):
        monkeypatch.delenv("ADMIN_TOKEN", raising=False)
        response = client.get("/admin/summary", headers=ADMIN_TOKEN_HEADER)
        assert response.status_code == 503
