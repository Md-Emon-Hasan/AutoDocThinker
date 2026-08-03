"""Consolidated tests for indexing and retrieval modules."""

from app.indexing.deduplication import already_ingested


class TestDeduplication:
    def test_ingested(self):
        assert already_ingested({"a"}, {"a"}) is True

    def test_not_ingested(self):
        assert already_ingested({"a"}, {"b"}) is False
