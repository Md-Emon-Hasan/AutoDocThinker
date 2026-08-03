"""Consolidated tests for indexing and retrieval modules."""

from app.indexing.chroma_store import ChromaStore


class TestChromaStore:
    def test_persist(self):
        assert ChromaStore().persist() is True
