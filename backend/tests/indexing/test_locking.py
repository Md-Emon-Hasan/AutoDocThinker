"""Consolidated tests for indexing and retrieval modules."""

from app.indexing.locking import new_lock


class TestLocking:
    def test_new_lock(self):
        lock = new_lock()
        assert hasattr(lock, "acquire") and hasattr(lock, "release")
