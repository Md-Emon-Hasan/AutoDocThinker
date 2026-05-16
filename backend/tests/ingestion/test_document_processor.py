"""Consolidated tests for the ingestion module: document, loaders, chunk_optimizer,
document_processor, file_validation, metadata, source_id, supported_types, service."""

from unittest.mock import MagicMock, patch

import pytest

from app.indexing.hybrid_index import HybridIndex
from app.ingestion.chunk_optimizer import ChunkOptimizer
from app.ingestion.document import Document
from app.ingestion.document_processor import DocumentProcessor
from app.ingestion.file_validation import ensure_supported_path
from app.ingestion.loaders.base import BaseLoader
from app.ingestion.loaders.docx_loader import DocxLoader
from app.ingestion.loaders.factory import get_loader
from app.ingestion.loaders.pdf_loader import PdfLoader
from app.ingestion.loaders.text_loader import TextLoader
from app.ingestion.loaders.txt_loader import TxtLoader
from app.ingestion.loaders.url_loader import UrlLoader
from app.ingestion.metadata import enrich_metadata
from app.ingestion.service import (
    IngestionService,
    auto_ingest_data_dir,
    ingest_documents,
    ingest_file,
)
from app.ingestion.source_id import make_source_id
from app.ingestion.supported_types import extension_to_type


class TestDocumentProcessor:
    def test_load_txt(self, tmp_path):
        f = tmp_path / "a.txt"
        f.write_text("hello", encoding="utf-8")
        docs = DocumentProcessor().load(str(f), "txt")
        assert docs[0].metadata["file_type"] == "txt"

    def test_load_with_display_name(self, tmp_path):
        f = tmp_path / "b.txt"
        f.write_text("content", encoding="utf-8")
        docs = DocumentProcessor().load(str(f), "txt", display_name="Custom")
        assert docs[0].metadata["source"] == "Custom"

    def test_load_url_uses_source_as_name(self):
        docs = DocumentProcessor().load("https://example.com", "url")
        assert docs[0].metadata["source"] == "https://example.com"

    def test_load_text_uses_pasted_text_name(self):
        docs = DocumentProcessor().load("Some pasted content", "text")
        assert docs[0].metadata["source"] == "pasted_text"

    def test_load_empty_raises(self):
        with pytest.raises(ValueError, match="empty"):
            DocumentProcessor().load("   ", "text")

    def test_load_returns_no_documents_raises(self):
        class EmptyLoader:
            def load(self, source):
                return []

        with (
            patch(
                "app.ingestion.document_processor.get_loader",
                return_value=EmptyLoader(),
            ),
            pytest.raises(ValueError, match="no documents"),
        ):
            DocumentProcessor().load("dummy", "txt")
