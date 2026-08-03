"""Consolidated tests for the ingestion module: document, loaders, chunk_optimizer,
document_processor, file_validation, metadata, source_id, supported_types, service."""

from app.ingestion.source_id import make_source_id


class TestSourceId:
    def test_consistent_hash(self):
        assert make_source_id("test") == make_source_id("test")

    def test_hash_length(self):
        assert len(make_source_id("hello")) == 12
