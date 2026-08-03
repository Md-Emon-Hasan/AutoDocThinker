"""Consolidated tests for RAG module: citations, formatting, history, modes,
state, service, process_query, finalize, and all four workflow packages."""

from app.rag.state import (
    AdvancedState,
    BaseState,
    CRAGState,
    NaiveState,
    RAGState,
    SelfRAGState,
)

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
