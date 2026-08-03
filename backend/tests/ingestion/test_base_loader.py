"""Consolidated tests for the ingestion module: document, loaders, chunk_optimizer,
document_processor, file_validation, metadata, source_id, supported_types, service."""

import pytest

from app.ingestion.loaders.base import BaseLoader


class TestBaseLoader:
    def test_is_abstract(self):
        with pytest.raises(TypeError):
            BaseLoader()
