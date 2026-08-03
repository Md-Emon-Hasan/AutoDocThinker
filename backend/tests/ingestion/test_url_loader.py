"""Consolidated tests for the ingestion module: document, loaders, chunk_optimizer,
document_processor, file_validation, metadata, source_id, supported_types, service."""

from app.ingestion.loaders.url_loader import UrlLoader


class TestUrlLoader:
    def test_load(self):
        docs = UrlLoader().load("https://example.com")
        assert "example.com" in docs[0].page_content
