"""Decay reduces confidence over time and drops stale facts out of
retrieval; DELETE removes episodic + semantic records AND their
embeddings from the Chroma collection; session deletion cascades."""

from app.memory.semantic import FactIndex
from app.memory.store import MemoryStore


class TestDecay:
    def test_decay_reduces_confidence(self, tmp_path):
        store = MemoryStore(tmp_path / "memory.sqlite3")
        fact = store.add_fact("session:s1", "old fact", confidence=1.0, now=0.0)
        store.decay_facts(
            "session:s1", half_life_seconds=100.0, min_confidence=0.0, now=100.0
        )
        decayed = store.get_fact(fact.id)
        assert decayed.confidence < 1.0
        assert abs(decayed.confidence - 0.5) < 0.01

    def test_low_confidence_facts_deactivated_not_deleted(self, tmp_path):
        store = MemoryStore(tmp_path / "memory.sqlite3")
        fact = store.add_fact("session:s1", "stale fact", confidence=0.2, now=0.0)
        store.decay_facts(
            "session:s1", half_life_seconds=10.0, min_confidence=0.15, now=1000.0
        )
        result = store.get_fact(fact.id)
        assert result is not None  # not deleted
        assert result.active is False  # but deactivated

    def test_deactivated_facts_excluded_from_default_listing(self, tmp_path):
        store = MemoryStore(tmp_path / "memory.sqlite3")
        store.add_fact("session:s1", "stale fact", confidence=0.2, now=0.0)
        store.decay_facts(
            "session:s1", half_life_seconds=10.0, min_confidence=0.15, now=1000.0
        )
        assert store.list_facts("session:s1") == []

    def test_healthy_facts_survive_decay(self, tmp_path):
        store = MemoryStore(tmp_path / "memory.sqlite3")
        store.add_fact("session:s1", "durable fact", confidence=0.99, now=0.0)
        store.decay_facts(
            "session:s1", half_life_seconds=1_000_000.0, min_confidence=0.01, now=1.0
        )
        assert len(store.list_facts("session:s1")) == 1


class TestDeletion:
    def test_delete_session_removes_episodic_and_semantic(self, tmp_path):
        store = MemoryStore(tmp_path / "memory.sqlite3")
        store.add_turn("s1", "user", "hello")
        store.add_fact("session:s1", "a fact", confidence=0.9)

        result = store.delete_session("s1")
        assert result["turns_removed"] == 1
        assert result["facts_removed"] == 1
        assert store.get_turns("s1")["total"] == 0
        assert store.list_facts("session:s1") == []

    def test_delete_session_removes_embeddings(self, tmp_path):
        index = FactIndex(persist_directory=tmp_path / "chroma_memory")
        index.add("f1", "session:s1", "a fact")
        removed = index.remove_scope("session:s1")
        assert removed == 1
        assert index.search("session:s1", "fact", k=10) == []

    def test_deletion_cascades_both_stores(self, tmp_path):
        store = MemoryStore(tmp_path / "memory.sqlite3")
        index = FactIndex(persist_directory=tmp_path / "chroma_memory")
        fact = store.add_fact("session:s1", "a fact", confidence=0.9)
        index.add(fact.id, "session:s1", fact.text)

        store.delete_session("s1")
        index.remove_scope("session:s1")

        assert store.list_facts("session:s1") == []
        assert index.search("session:s1", "fact", k=10) == []
