"""Consolidated tests for the ingestion module: document, loaders, chunk_optimizer,
document_processor, file_validation, metadata, source_id, supported_types, service."""

import pytest

from app.ingestion.loaders.factory import get_loader


class TestLoaderFactory:
    def test_all_types(self):
        for t in ("txt", "text", "url", "pdf", "docx"):
            assert get_loader(t) is not None

    def test_unsupported_raises(self):
        with pytest.raises(ValueError, match="Unsupported"):
            get_loader("xyz")
