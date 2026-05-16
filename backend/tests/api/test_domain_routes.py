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


class TestDomainRoutes:
    def test_list_domains_returns_200(self, client):
        response = client.get("/domains")
        assert response.status_code == 200
        names = [d["name"] for d in response.json()]
        assert "general" in names
        assert "legal" in names

    def test_get_domain_by_name(self, client):
        response = client.get("/domains/legal")
        assert response.status_code == 200
        assert response.json()["name"] == "legal"
        assert response.json()["label"] == "Legal"

    def test_get_missing_domain_returns_404(self, client):
        response = client.get("/domains/missing")
        assert response.status_code == 404


# ── chat sessions ────────────────────────────────────────────────────────────
