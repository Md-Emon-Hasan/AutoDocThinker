"""Consolidated tests for the ingestion module: document, loaders, chunk_optimizer,
document_processor, file_validation, metadata, source_id, supported_types, service."""

from app.ingestion.document import Document


class TestDocument:
    def test_default_metadata(self):
        doc = Document("text")
        assert doc.metadata == {}

    def test_with_metadata(self):
        doc = Document("text", {"key": "val"})
        assert doc.metadata["key"] == "val"
