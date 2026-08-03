"""Consolidated tests for the ingestion module: document, loaders, chunk_optimizer,
document_processor, file_validation, metadata, source_id, supported_types, service."""

import pytest

from app.ingestion.file_validation import ensure_supported_path


class TestFileValidation:
    def test_valid(self, tmp_path):
        f = tmp_path / "note.txt"
        f.write_text("hello", encoding="utf-8")
        assert ensure_supported_path(str(f), (".txt",)) == f

    def test_unsupported_raises(self):
        with pytest.raises(ValueError):
            ensure_supported_path("bad.md", (".txt",))
