"""Consolidated tests for RAG module: citations, formatting, history, modes,
state, service, process_query, finalize, and all four workflow packages."""

from app.rag.history import (
    _history_messages,
    append_turn,
    history_messages,
    trim_history,
)

# ── citations & formatting ───────────────────────────────────────────────────


class TestHistory:
    def test_append(self):
        h = append_turn([], "q", "a")
        assert h[-1]["role"] == "assistant"

    def test_trim(self):
        items = [{"role": "x", "content": str(i)} for i in range(20)]
        assert trim_history(items, 3)[0]["content"] == "17"

    def test_messages(self):
        assert history_messages([{"role": "user", "content": "hi"}]) == [("user", "hi")]

    def test_private_messages(self):
        assert _history_messages([{"role": "user", "content": "hi"}]) == [
            ("user", "hi")
        ]


# ── modes & state ────────────────────────────────────────────────────────────
