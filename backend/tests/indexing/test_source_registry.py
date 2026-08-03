"""Consolidated tests for indexing and retrieval modules."""

from app.indexing.source_registry import SourceRegistry


class TestSourceRegistry:
    def test_add(self):
        r = SourceRegistry()
        r.add("src1")
        assert "src1" in r.sources
