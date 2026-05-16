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


class TestChunkOptimizer:
    def test_splits_large_document(self, tmp_path):
        source = tmp_path / "note.txt"
        source.write_text("alpha beta gamma " * 80, encoding="utf-8")
        docs = DocumentProcessor().load(str(source), "txt")
        chunks = ChunkOptimizer(chunk_size=40, chunk_overlap=10).split(docs, "txt")
        assert len(chunks) > 1

    def test_empty_returns_no_chunks(self):
        assert ChunkOptimizer().split([Document("   ")], "url") == []

    def test_pdf_chunk_size(self):
        chunks = ChunkOptimizer().split([Document("pdf text")], "pdf")
        assert chunks[0].page_content == "pdf text"

    def test_url_chunk_size(self):
        chunks = ChunkOptimizer().split([Document("url text content")], "url")
        assert chunks[0].page_content == "url text content"
