"""Consolidated tests for the ingestion module: document, loaders, chunk_optimizer,
document_processor, file_validation, metadata, source_id, supported_types, service."""

from unittest.mock import MagicMock, patch

import pytest

from app.ingestion.loaders.pdf_loader import PdfLoader


class TestPdfLoader:
    def test_load_success(self):
        mock_fitz = MagicMock()
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "pdf content"
        mock_pdf.__iter__.return_value = [mock_page]
        mock_pdf.__enter__.return_value = mock_pdf
        mock_fitz.open.return_value = mock_pdf

        with patch.dict("sys.modules", {"fitz": mock_fitz}):
            docs = PdfLoader().load("dummy.pdf")
            assert docs[0].page_content == "pdf content"

    def test_import_error(self):
        with (
            patch.dict("sys.modules", {"fitz": None}),
            pytest.raises(RuntimeError, match="PDF loading requires pymupdf"),
        ):
            PdfLoader().load("dummy.pdf")
