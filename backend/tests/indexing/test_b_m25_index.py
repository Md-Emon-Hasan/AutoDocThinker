"""Consolidated tests for indexing and retrieval modules."""

from app.indexing.bm25_index import BM25Index


class TestBM25Index:
    def test_match(self):
        assert BM25Index().score("alpha beta", "alpha beta gamma") > 0

    def test_no_match(self):
        assert BM25Index().score("xyz", "alpha beta") == 0
