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


class TestIngestionService:
    def test_ingest(self, tmp_path):
        source = tmp_path / "note.txt"
        source.write_text("alpha beta gamma " * 80, encoding="utf-8")
        result = IngestionService(HybridIndex()).ingest(str(source), "txt")
        assert result["chunks_added"] >= 1

    def test_duplicate_returns_zero(self, tmp_path):
        source = tmp_path / "note.txt"
        source.write_text("alpha beta gamma " * 80, encoding="utf-8")
        svc = IngestionService(HybridIndex())
        svc.ingest(str(source), "txt")
        assert svc.ingest(str(source), "txt")["chunks_added"] == 0

    def test_auto_ingest(self, tmp_path):
        data = tmp_path / "data"
        data.mkdir()
        (data / "a.txt").write_text("hello world alpha", encoding="utf-8")
        result = IngestionService(HybridIndex()).auto_ingest(data, (".txt",))
        assert result["ingested"] == ["a.txt"]

    def test_auto_ingest_skips_duplicates(self, tmp_path):
        data = tmp_path / "data"
        data.mkdir()
        (data / "a.txt").write_text("hello world alpha", encoding="utf-8")
        svc = IngestionService(HybridIndex())
        svc.auto_ingest(data, (".txt",))
        assert svc.auto_ingest(data, (".txt",))["skipped"] == ["a.txt"]

    def test_auto_ingest_handles_failures(self, tmp_path):
        data = tmp_path / "data"
        data.mkdir()
        (data / "a.txt").write_text("hi", encoding="utf-8")

        class BadProcessor:
            def load(self, *a, **kw):
                raise ValueError("bad")

        result = IngestionService(HybridIndex(), processor=BadProcessor()).auto_ingest(
            data, (".txt",)
        )
        assert result["failed"]
