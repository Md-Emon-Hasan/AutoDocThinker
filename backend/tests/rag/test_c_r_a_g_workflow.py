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


class TestCRAGWorkflow:
    def test_ingest(self, rag_state):
        assert crag_ingest(rag_state) is rag_state

    def test_retrieve(self, rag_state, seeded_container):
        assert "context_docs" in crag_retrieve(rag_state, seeded_container["retrieval"])

    def test_evaluate(self, rag_state, seeded_container):
        retrieved = crag_retrieve(rag_state, seeded_container["retrieval"])
        assert "confidence" in crag_evaluate(retrieved)

    def test_web_search(self, rag_state, seeded_container):
        box = seeded_container
        evaluated = crag_evaluate(crag_retrieve(rag_state, box["retrieval"]))
        assert crag_web_search(evaluated, box["rag"].wiki)["confidence"] >= 0.6

    def test_answer(self, rag_state, seeded_container):
        box = seeded_container
        profile = box["domains"].get("general")
        searched = crag_web_search(
            crag_evaluate(crag_retrieve(rag_state, box["retrieval"])), box["rag"].wiki
        )
        assert crag_answer(searched, box["rag"].llm, profile)["answer"]

    def test_build(self, rag_state, seeded_container):
        box = seeded_container
        profile = box["domains"].get("general")
        assert build_crag(box["retrieval"], box["rag"].llm, profile, box["rag"].wiki)(
            rag_state
        )["answer"]

    def test_edges(self):
        assert needs_web_search({"confidence": 0.3})
        assert not needs_web_search({"confidence": 0.8})


# ── self-RAG workflow ────────────────────────────────────────────────────────
