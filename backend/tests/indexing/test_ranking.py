"""Consolidated tests for indexing and retrieval modules."""

from app.retrieval.ranking import top_k


class TestRanking:
    def test_top_k(self):
        assert top_k([1, 2, 3, 4], 2) == [1, 2]
