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


class TestStandaloneFunctions:
    def test_ingest_documents(self, tmp_path):
        f = tmp_path / "other.txt"
        f.write_text("new source alpha", encoding="utf-8")
        assert ingest_documents(HybridIndex(), str(f), "txt") >= 1

    def test_ingest_file(self, tmp_path):
        f = tmp_path / "other.txt"
        f.write_text("new source alpha", encoding="utf-8")
        idx = HybridIndex()
        ingest_documents(idx, str(f), "txt")
        assert ingest_file(idx, str(f), "txt")["chunks_added"] == 0

    def test_auto_ingest_data_dir(self, tmp_path):
        data = tmp_path / "data"
        data.mkdir()
        (data / "a.txt").write_text("hello world", encoding="utf-8")
        assert auto_ingest_data_dir(HybridIndex(), data, (".txt",))["ingested"] == [
            "a.txt"
        ]
