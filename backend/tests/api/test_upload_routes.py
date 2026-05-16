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


class TestUploadRoutes:
    def test_upload_txt_file(self, client):
        content = b"this is test upload content alpha beta gamma delta"
        response = client.post(
            "/ingest/upload",
            files={"file": ("test.txt", io.BytesIO(content), "text/plain")},
        )
        assert response.status_code == 200
        assert response.json()["chunks_added"] >= 1

    def test_upload_save_error(self, client):
        from unittest.mock import patch

        with patch(
            "pathlib.Path.write_bytes", side_effect=Exception("mock write error")
        ):
            response = client.post(
                "/ingest/upload",
                files={"file": ("test.txt", io.BytesIO(b"data"), "text/plain")},
            )
            assert response.status_code == 500

    def test_upload_file_not_persisted(self, client):
        from unittest.mock import patch

        with (
            patch("pathlib.Path.write_bytes"),
            patch("pathlib.Path.exists", return_value=False),
        ):
            response = client.post(
                "/ingest/upload",
                files={"file": ("test.txt", io.BytesIO(b"data"), "text/plain")},
            )
            assert response.status_code == 500

    def test_upload_ingest_error(self, client):
        from unittest.mock import patch

        with patch(
            "app.ingestion.service.IngestionService.ingest",
            side_effect=Exception("mock ingest error"),
        ):
            response = client.post(
                "/ingest/upload",
                files={"file": ("test.txt", io.BytesIO(b"data"), "text/plain")},
            )
            assert response.status_code == 400

    def test_upload_unsupported_extension_returns_400(self, client):
        response = client.post(
            "/ingest/upload",
            files={"file": ("test.csv", io.BytesIO(b"csv data"), "text/csv")},
        )
        assert response.status_code == 400

    def test_upload_empty_file_returns_400(self, client):
        response = client.post(
            "/ingest/upload",
            files={"file": ("empty.txt", io.BytesIO(b""), "text/plain")},
        )
        assert response.status_code == 400
