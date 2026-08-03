"""Consolidated tests for indexing and retrieval modules."""

from app.indexing.tokenizer import tokenize


class TestTokenizer:
    def test_lowercases(self):
        assert tokenize("Hello WORLD") == ["hello", "world"]

    def test_empty(self):
        assert tokenize("") == []
