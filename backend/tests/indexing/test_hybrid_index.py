"""Consolidated tests for indexing and retrieval modules."""


class TestHybridIndex:
    def test_add_and_size(self, fresh_index, sample_documents):
        assert fresh_index.add(sample_documents) == 2
        assert fresh_index.size == 2

    def test_duplicate_returns_zero(self, populated_index, sample_documents):
        assert populated_index.add(sample_documents) == 0

    def test_add_empty(self, fresh_index):
        assert fresh_index.add([]) == 0

    def test_search(self, populated_index):
        assert len(populated_index.search("alpha beta")) >= 1

    def test_search_with_filter(self, populated_index):
        results = populated_index.search("alpha", metadata_filter={"kind": "a"})
        assert all(r.metadata["kind"] == "a" for r in results)

    def test_search_empty_query(self, populated_index):
        results = populated_index.search("")
        assert len(results) == 0

    def test_sources_sorted(self, populated_index):
        assert populated_index.sources == sorted(populated_index.sources)

    def test_source_details(self, populated_index):
        assert len(populated_index.source_details) >= 1

    def test_clear(self, populated_index):
        populated_index.clear()
        assert populated_index.size == 0

    def test_remove_source(self, populated_index):
        assert populated_index.remove_source("s1") is True
        assert populated_index.remove_source("s1") is False
