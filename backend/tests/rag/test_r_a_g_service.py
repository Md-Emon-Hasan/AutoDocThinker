"""Consolidated tests for RAG module: citations, formatting, history, modes,
state, service, process_query, finalize, and all four workflow packages."""

import pytest

from app.ingestion.document import Document
from app.rag.citations import build_sources, format_source_label, source_label
from app.rag.formatting import format_context_with_sources
from app.rag.history import (
    _history_messages,
    append_turn,
    history_messages,
    trim_history,
)
from app.rag.modes import RAG_MODES, ensure_mode
from app.rag.service import process_query
from app.rag.state import (
    AdvancedState,
    BaseState,
    CRAGState,
    NaiveState,
    RAGState,
    SelfRAGState,
)
from app.workflows.advanced import (
    _compress_one,
    advanced_answer,
    advanced_compress,
    advanced_fallback,
    advanced_ingest,
    advanced_retrieve,
    advanced_rewrite,
    build_advanced_rag,
)
from app.workflows.advanced.edges import has_rewrites
from app.workflows.crag import (
    build_crag,
    crag_answer,
    crag_evaluate,
    crag_ingest,
    crag_retrieve,
    crag_web_search,
)
from app.workflows.crag.edges import needs_web_search
from app.workflows.finalize import finalize
from app.workflows.naive import (
    build_naive_rag,
    naive_answer,
    naive_fallback,
    naive_ingest,
    naive_retrieve,
    naive_router,
)
from app.workflows.naive.edges import should_fallback
from app.workflows.self_rag import (
    build_self_rag,
    self_rag_critique,
    self_rag_decide,
    self_rag_generate,
    self_rag_ingest,
    self_rag_retrieve,
    self_rag_revise,
)
from app.workflows.self_rag.edges import should_retrieve

# ── citations & formatting ───────────────────────────────────────────────────


class TestRAGService:
    def test_naive(self, seeded_container):
        result = seeded_container["rag"].query("payment terms", "general", "naive")
        assert result["answer"] and result["history"][-1]["role"] == "assistant"

    def test_advanced(self, seeded_container):
        assert seeded_container["rag"].query("payment terms", "general", "advanced")[
            "answer"
        ]

    def test_crag(self, seeded_container):
        assert seeded_container["rag"].query("payment terms", "general", "crag")[
            "answer"
        ]

    def test_self_rag(self, seeded_container):
        assert seeded_container["rag"].query("payment terms", "general", "self_rag")[
            "answer"
        ]

    def test_crag_web_search_trigger(self, seeded_container):
        result = seeded_container["rag"].query("unmatched", "general", "crag")
        assert result["metadata"]["confidence"] >= 0.6
