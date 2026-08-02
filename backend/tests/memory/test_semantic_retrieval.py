"""Fact retrieval is vector search over a SEPARATE Chroma collection
from documents, hard-filtered by scope. A memory leak across sessions
is the same privacy defect as a document leak."""

from app.memory.semantic import FactIndex


class TestSemanticRetrieval:
    def test_scope_filtered_search(self, tmp_path):
        index = FactIndex(persist_directory=tmp_path / "chroma_memory")
        index.add("f1", "session:a", "likes dark mode")
        index.add("f2", "session:b", "likes light mode")

        results_a = index.search("session:a", "mode preference", k=10)
        assert "f1" in results_a
        assert "f2" not in results_a

    def test_cross_session_leak_test(self, tmp_path):
        index = FactIndex(persist_directory=tmp_path / "chroma_memory")
        index.add(
            "secret-fact", "session:private", "the user's secret project name is X"
        )
        results = index.search("session:other", "secret project name", k=10)
        assert "secret-fact" not in results

    def test_separate_collection_from_documents(self, tmp_path):
        """FactIndex uses its own 'memory_facts' collection name --
        never mixed into app/indexing/chroma_store.py's document
        collections."""
        index = FactIndex(persist_directory=tmp_path / "chroma_memory")
        assert index._collection.name == "memory_facts"

    def test_remove_scope(self, tmp_path):
        index = FactIndex(persist_directory=tmp_path / "chroma_memory")
        index.add("f1", "session:a", "fact one")
        index.add("f2", "session:a", "fact two")
        removed = index.remove_scope("session:a")
        assert removed == 2
        assert index.search("session:a", "fact", k=10) == []
