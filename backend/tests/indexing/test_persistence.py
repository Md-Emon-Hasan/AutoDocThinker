"""Consolidated tests for indexing and retrieval modules."""

from app.indexing.persistence import snapshot_index


class TestPersistence:
    def test_snapshot(self, populated_index):
        assert snapshot_index(populated_index)["total_chunks"] == populated_index.size
