"""Consolidated tests for indexing and retrieval modules."""

from app.indexing.stats import index_stats


class TestStats:
    def test_stats(self, populated_index):
        assert index_stats(populated_index)["source_count"] == len(
            populated_index.sources
        )
