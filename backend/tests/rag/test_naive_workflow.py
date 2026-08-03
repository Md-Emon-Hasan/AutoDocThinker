"""Consolidated tests for RAG module: citations, formatting, history, modes,
state, service, process_query, finalize, and all four workflow packages."""

from app.ingestion.document import Document
from app.workflows.naive import (
    build_naive_rag,
    naive_answer,
    naive_fallback,
    naive_ingest,
    naive_retrieve,
    naive_router,
)
from app.workflows.naive.edges import should_fallback

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
