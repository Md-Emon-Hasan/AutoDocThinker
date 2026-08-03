"""Consolidated tests for indexing and retrieval modules."""

from app.retrieval.bm25_search import bm25_search


class TestBM25Search:
    def test_results(self, populated_index):
        assert len(bm25_search(populated_index, "alpha", 5)) >= 1
