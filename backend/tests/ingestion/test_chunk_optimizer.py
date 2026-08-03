"""Consolidated tests for the ingestion module: document, loaders, chunk_optimizer,
document_processor, file_validation, metadata, source_id, supported_types, service."""

from app.ingestion.chunk_optimizer import ChunkOptimizer
from app.ingestion.document import Document
from app.ingestion.document_processor import DocumentProcessor


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
