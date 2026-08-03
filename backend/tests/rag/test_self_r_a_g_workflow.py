"""Consolidated tests for RAG module: citations, formatting, history, modes,
state, service, process_query, finalize, and all four workflow packages."""

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


class TestSelfRAGWorkflow:
    def test_ingest(self, rag_state):
        assert self_rag_ingest(rag_state) is rag_state

    def test_decide(self, rag_state, seeded_container):
        assert "need_retrieval" in self_rag_decide(
            rag_state, seeded_container["retrieval"]
        )

    def test_retrieve(self, rag_state, seeded_container):
        assert "context_docs" in self_rag_retrieve(
            rag_state, seeded_container["retrieval"]
        )

    def test_generate(self, rag_state, seeded_container):
        box = seeded_container
        decided = self_rag_decide(rag_state, box["retrieval"])
        assert self_rag_generate(
            decided, box["rag"].llm, box["domains"].get("general")
        )["answer"]

    def test_critique(self, rag_state, seeded_container):
        box = seeded_container
        decided = self_rag_decide(rag_state, box["retrieval"])
        generated = self_rag_generate(
            decided, box["rag"].llm, box["domains"].get("general")
        )
        assert self_rag_critique(generated)["critique"] == "No issues detected."

    def test_revise(self):
        assert self_rag_revise({"draft_answer": "revised"})["answer"] == "revised"
        assert self_rag_revise({"answer": "original"})["answer"] == "original"

    def test_build(self, rag_state, seeded_container):
        box = seeded_container
        profile = box["domains"].get("general")
        assert build_self_rag(box["retrieval"], box["rag"].llm, profile)(rag_state)[
            "answer"
        ]

    def test_edges(self):
        assert should_retrieve({"need_retrieval": True})
        assert not should_retrieve({"need_retrieval": False})
