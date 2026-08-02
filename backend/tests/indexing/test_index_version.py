"""Tests for HybridIndex's monotonic version counter (Stage 2 cache key)."""

from app.ingestion.document import Document


class TestIndexVersion:
    def test_starts_at_zero(self, fresh_index):
        assert fresh_index.version == 0

    def test_bumps_on_add(self, fresh_index, sample_documents):
        fresh_index.add(sample_documents)
        assert fresh_index.version == 1

    def test_bumps_on_remove_source(self, populated_index):
        before = populated_index.version
        populated_index.remove_source("s1")
        assert populated_index.version == before + 1

    def test_bumps_on_clear(self, populated_index):
        before = populated_index.version
        populated_index.clear()
        assert populated_index.version == before + 1

    def test_bumps_on_remove_scope(self, fresh_index):
        fresh_index.add([Document("alpha", {"source_id": "s1", "scope": "session:a"})])
        before = fresh_index.version
        fresh_index.remove_scope("session:a")
        assert fresh_index.version == before + 1

    def test_no_op_add_does_not_bump(self, populated_index, sample_documents):
        before = populated_index.version
        # Duplicate source_ids -> rejected batch, version must not bump.
        populated_index.add(sample_documents)
        assert populated_index.version == before

    def test_no_op_remove_does_not_bump(self, populated_index):
        before = populated_index.version
        populated_index.remove_source("nonexistent")
        assert populated_index.version == before

    def test_stale_key_misses_after_bump(self, fresh_index):
        from app.utils.cache import MISSING, TTLCacheLayer

        cache = TTLCacheLayer(maxsize=10, ttl=60)
        fresh_index.add([Document("alpha", {"source_id": "s1"})])
        key = f"query::{fresh_index.version}"
        cache.set(key, "cached answer")
        assert cache.get(key) == "cached answer"

        fresh_index.add([Document("beta", {"source_id": "s2"})])
        stale_key = f"query::{fresh_index.version - 1}"
        assert stale_key == key
        fresh_key = f"query::{fresh_index.version}"
        assert cache.get(fresh_key) is MISSING
