"""Consolidated tests for indexing and retrieval modules."""

from app.indexing.vector_index import VectorIndex


class TestVectorIndex:
    def test_similar(self):
        assert VectorIndex().similarity("abc", "abd") > 0

    def test_identical(self):
        assert VectorIndex().similarity("abc", "abc") == 1.0
