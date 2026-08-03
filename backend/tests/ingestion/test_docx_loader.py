"""Consolidated tests for the ingestion module: document, loaders, chunk_optimizer,
document_processor, file_validation, metadata, source_id, supported_types, service."""

from unittest.mock import patch

import pytest

from app.ingestion.loaders.docx_loader import DocxLoader


class TestDocxLoader:
    def test_load_success(self):
        with patch("docx2txt.process", return_value="docx content"):
            docs = DocxLoader().load("dummy.docx")
            assert docs[0].page_content == "docx content"

    def test_import_error(self):
        with (
            patch.dict("sys.modules", {"docx2txt": None}),
            pytest.raises(RuntimeError, match="DOCX loading requires docx2txt"),
        ):
            DocxLoader().load("dummy.docx")
