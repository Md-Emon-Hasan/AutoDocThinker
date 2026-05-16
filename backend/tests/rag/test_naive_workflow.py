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


class TestNaiveWorkflow:
    def test_ingest(self, rag_state):
        assert naive_ingest(rag_state) is rag_state

    def test_retrieve(self, rag_state, seeded_container):
        assert "context_docs" in naive_retrieve(
            rag_state, seeded_container["retrieval"]
        )

    def test_router_fallback(self):
        assert naive_router({"context_docs": []})["next_agent"] == "fallback"

    def test_router_answer(self):
        assert (
            naive_router({"context_docs": [Document("x", {})]})["next_agent"]
            == "answer"
        )

    def test_answer(self, rag_state, seeded_container):
        box = seeded_container
        retrieved = naive_retrieve(rag_state, box["retrieval"])
        assert naive_answer(retrieved, box["rag"].llm, box["domains"].get("general"))[
            "answer"
        ]

    def test_fallback(self, rag_state, seeded_container):
        box = seeded_container
        assert naive_fallback(rag_state, box["rag"].llm, box["domains"].get("general"))[
            "answer"
        ]

    def test_build(self, rag_state, seeded_container):
        box = seeded_container
        fn = build_naive_rag(
            box["retrieval"], box["rag"].llm, box["domains"].get("general")
        )
        assert fn(rag_state)["answer"]

    def test_edges(self):
        assert should_fallback({"context_docs": []})
        assert not should_fallback({"context_docs": [Document("x", {})]})


# ── advanced workflow ────────────────────────────────────────────────────────
