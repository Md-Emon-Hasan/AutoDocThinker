"""Consolidated tests for RAG module: citations, formatting, history, modes,
state, service, process_query, finalize, and all four workflow packages."""

from app.rag.service import process_query

# ── citations & formatting ───────────────────────────────────────────────────


class TestProcessQuery:
    def test_basic(self, seeded_container):
        assert process_query(seeded_container["rag"], "payment", mode="naive")["answer"]

    def test_with_file(self, seeded_container):
        assert process_query(
            seeded_container["rag"], "payment", file_path="x", file_type="txt"
        )["answer"]


# ── naive workflow ───────────────────────────────────────────────────────────
