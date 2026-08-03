"""Consolidated tests for indexing and retrieval modules."""

from app.ingestion.document import Document
from app.retrieval.compressor import compress_documents


class TestCompressor:
    def test_truncates(self):
        doc = Document("x" * 5000, {})
        compress_documents([doc], max_chars=100)
        assert len(doc.page_content) <= 100

    def test_preserves(self):
        doc = Document("short", {})
        compress_documents([doc])
        assert doc.page_content == "short"
