"""Consolidated tests for the ingestion module: document, loaders, chunk_optimizer,
document_processor, file_validation, metadata, source_id, supported_types, service."""

from unittest.mock import patch

import pytest

from app.ingestion.document_processor import DocumentProcessor


class TestDocumentProcessor:
    def test_load_txt(self, tmp_path):
        f = tmp_path / "a.txt"
        f.write_text("hello", encoding="utf-8")
        docs = DocumentProcessor().load(str(f), "txt")
        assert docs[0].metadata["file_type"] == "txt"

    def test_load_with_display_name(self, tmp_path):
        f = tmp_path / "b.txt"
        f.write_text("content", encoding="utf-8")
        docs = DocumentProcessor().load(str(f), "txt", display_name="Custom")
        assert docs[0].metadata["source"] == "Custom"

    def test_load_url_uses_source_as_name(self):
        docs = DocumentProcessor().load("https://example.com", "url")
        assert docs[0].metadata["source"] == "https://example.com"

    def test_load_text_uses_pasted_text_name(self):
        docs = DocumentProcessor().load("Some pasted content", "text")
        assert docs[0].metadata["source"] == "pasted_text"

    def test_load_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            DocumentProcessor().load("   ", "text")

    def test_load_returns_no_documents_raises(self):
        class EmptyLoader:
            def load(self, source):
                return []

        with (
            patch(
                "app.ingestion.document_processor.get_loader",
                return_value=EmptyLoader(),
            ),
            pytest.raises(ValueError, match="no documents"),
        ):
            DocumentProcessor().load("dummy", "txt")
