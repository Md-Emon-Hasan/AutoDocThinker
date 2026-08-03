"""Consolidated tests for RAG module: citations, formatting, history, modes,
state, service, process_query, finalize, and all four workflow packages."""

from app.workflows.crag import (
    build_crag,
    crag_answer,
    crag_evaluate,
    crag_ingest,
    crag_retrieve,
    crag_web_search,
)
from app.workflows.crag.edges import needs_web_search

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
