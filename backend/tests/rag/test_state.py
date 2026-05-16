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


class TestState:
    def test_types(self):
        assert BaseState(input="x")["input"] == "x"
        assert NaiveState(next_agent="a")["next_agent"] == "a"
        assert AdvancedState(rewritten_queries=["x"])["rewritten_queries"] == ["x"]
        assert CRAGState(retrieval_score=1)["retrieval_score"] == 1
        assert SelfRAGState(need_retrieval=True)["need_retrieval"] is True
        assert RAGState(input="x")["input"] == "x"


# ── finalize ─────────────────────────────────────────────────────────────────
