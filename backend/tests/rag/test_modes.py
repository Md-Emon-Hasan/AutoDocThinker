"""Consolidated tests for RAG module: citations, formatting, history, modes,
state, service, process_query, finalize, and all four workflow packages."""

import pytest

from app.rag.modes import RAG_MODES, ensure_mode

# ── citations & formatting ───────────────────────────────────────────────────


class TestModes:
    def test_valid(self):
        for m in RAG_MODES:
            assert ensure_mode(m) == m

    def test_case_insensitive(self):
        assert ensure_mode("CRAG") == "crag"

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            ensure_mode("bad")
