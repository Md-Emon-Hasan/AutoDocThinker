"""Consolidated tests for the ingestion module: document, loaders, chunk_optimizer,
document_processor, file_validation, metadata, source_id, supported_types, service."""

import pytest

from app.ingestion.loaders.text_loader import TextLoader


class TestTextLoader:
    def test_load(self):
        docs = TextLoader().load("Hello World")
        assert docs[0].page_content == "Hello World"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            TextLoader().load("   ")
