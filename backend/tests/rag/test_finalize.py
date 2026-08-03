"""Consolidated tests for RAG module: citations, formatting, history, modes,
state, service, process_query, finalize, and all four workflow packages."""

from app.workflows.finalize import finalize

# ── citations & formatting ───────────────────────────────────────────────────


class TestFinalize:
    def test_appends_history(self):
        state = {"input": "q", "answer": "a", "history": []}
        assert len(finalize(state)["history"]) == 2


# ── RAG service ──────────────────────────────────────────────────────────────
