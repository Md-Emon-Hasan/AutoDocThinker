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


class TestFileValidation:
    def test_valid(self, tmp_path):
        f = tmp_path / "note.txt"
        f.write_text("hello", encoding="utf-8")
        assert ensure_supported_path(str(f), (".txt",)) == f

    def test_unsupported_raises(self):
        with pytest.raises(ValueError):
            ensure_supported_path("bad.md", (".txt",))
