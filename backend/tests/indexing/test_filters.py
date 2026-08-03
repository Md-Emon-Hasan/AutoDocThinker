"""Consolidated tests for indexing and retrieval modules."""

from app.retrieval.filters import matches_filter


class TestFilters:
    def test_match(self):
        assert matches_filter({"k": "v"}, {"k": "v"}) is True

    def test_no_match(self):
        assert matches_filter({"k": "v"}, {"k": "x"}) is False

    def test_none(self):
        assert matches_filter({}, None) is True
