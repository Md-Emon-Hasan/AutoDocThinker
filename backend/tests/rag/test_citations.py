"""Consolidated tests for RAG module: citations, formatting, history, modes,
state, service, process_query, finalize, and all four workflow packages."""

from app.ingestion.document import Document
from app.rag.citations import build_sources, format_source_label, source_label
from app.rag.formatting import format_context_with_sources

# ── citations & formatting ───────────────────────────────────────────────────


class TestCitations:
    def test_with_page(self):
        assert source_label({"source": "s", "page": 1}) == "s p.1"

    def test_without_page(self):
        assert source_label({"source": "s"}) == "s"

    def test_empty(self):
        assert source_label({}) == "unknown"

    def test_format_source_label(self):
        assert format_source_label({"source": "s", "page": 2}) == "s p.2"

    def test_build_sources(self):
        doc = Document("text", {"source": "a", "page": 2, "chunk_id": "c"})
        sources = build_sources([doc])
        assert sources[0]["label"] == "a p.2" and sources[0]["id"] == 1

    def test_format_context(self):
        doc = Document("text", {"source": "a", "page": 2, "chunk_id": "c"})
        ctx, src = format_context_with_sources([doc])
        assert "[1]" in ctx and src[0]["label"] == "a p.2"


# ── history ──────────────────────────────────────────────────────────────────
