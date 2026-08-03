"""Consolidated tests for indexing and retrieval modules."""

from app.retrieval.vector_search import vector_search


class TestVectorSearch:
    def test_results(self, populated_index):
        assert len(vector_search(populated_index, "alpha", 5)) >= 1
