"""Consolidated tests for indexing and retrieval modules."""

from app.retrieval.hybrid_search import hybrid_search


class TestHybridSearch:
    def test_results(self, populated_index):
        assert len(hybrid_search(populated_index, "alpha", 5)) >= 1
