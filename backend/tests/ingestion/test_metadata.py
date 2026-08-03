"""Consolidated tests for the ingestion module: document, loaders, chunk_optimizer,
document_processor, file_validation, metadata, source_id, supported_types, service."""

from app.ingestion.metadata import enrich_metadata


class TestMetadata:
    def test_enrich(self):
        result = enrich_metadata({}, "s", "id", "txt")
        assert result["source_id"] == "id" and "ingested_at" in result
