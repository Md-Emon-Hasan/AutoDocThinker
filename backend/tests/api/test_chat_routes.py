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


class TestChatRoutes:
    def test_create_session(self, seeded_client):
        response = seeded_client.post("/chat/sessions")
        assert response.status_code == 200
        assert "session_id" in response.json()

    def test_get_session(self, seeded_client):
        session = seeded_client.post("/chat/sessions").json()
        response = seeded_client.get(f"/chat/sessions/{session['session_id']}")
        assert response.status_code == 200

    def test_get_missing_session_returns_404(self, seeded_client):
        assert seeded_client.get("/chat/sessions/missing").status_code == 404

    def test_select_profile_success(self, seeded_client):
        sid = seeded_client.post("/chat/sessions").json()["session_id"]
        response = seeded_client.post(
            f"/chat/sessions/{sid}/select-profile",
            json={"domain": "legal", "rag_mode": "crag"},
        )
        assert response.json()["domain"] == "legal"

    def test_select_profile_bad_domain_returns_404(self, seeded_client):
        sid = seeded_client.post("/chat/sessions").json()["session_id"]
        response = seeded_client.post(
            f"/chat/sessions/{sid}/select-profile",
            json={"domain": "bad", "rag_mode": "crag"},
        )
        assert response.status_code == 404

    def test_select_profile_bad_mode_returns_422(self, seeded_client):
        sid = seeded_client.post("/chat/sessions").json()["session_id"]
        response = seeded_client.post(
            f"/chat/sessions/{sid}/select-profile",
            json={"domain": "legal", "rag_mode": "bad"},
        )
        assert response.status_code == 422

    def test_send_message_success(self, seeded_client):
        sid = seeded_client.post("/chat/sessions").json()["session_id"]
        response = seeded_client.post(
            f"/chat/sessions/{sid}/messages", json={"message": "refund policy"}
        )
        assert response.status_code == 200

    def test_send_message_bad_mode_returns_422(self, seeded_client):
        sid = seeded_client.post("/chat/sessions").json()["session_id"]
        container()["chat"].get(sid).rag_mode = "bad"
        response = seeded_client.post(
            f"/chat/sessions/{sid}/messages", json={"message": "refund policy"}
        )
        assert response.status_code == 422

    def test_send_message_missing_session_returns_404(self, seeded_client):
        response = seeded_client.post(
            "/chat/sessions/missing/messages", json={"message": "x"}
        )
        assert response.status_code == 404

    def test_send_message_rate_limit_error(self, seeded_client):
        sid = seeded_client.post("/chat/sessions").json()["session_id"]
        from unittest.mock import patch

        with patch(
            "app.chat.service.ChatService.message",
            side_effect=RuntimeError("rate limit reached"),
        ):
            response = seeded_client.post(
                f"/chat/sessions/{sid}/messages", json={"message": "x"}
            )
            assert response.status_code == 429

    def test_send_message_runtime_error(self, seeded_client):
        sid = seeded_client.post("/chat/sessions").json()["session_id"]
        from unittest.mock import patch

        with patch(
            "app.chat.service.ChatService.message",
            side_effect=RuntimeError("other error"),
        ):
            response = seeded_client.post(
                f"/chat/sessions/{sid}/messages", json={"message": "x"}
            )
            assert response.status_code == 500


# ── ingestion ────────────────────────────────────────────────────────────────
