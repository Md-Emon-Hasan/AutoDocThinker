"""Tests for app/memory/store.py::MemoryStore -- the shared episodic +
semantic store."""

from app.memory.store import MemoryStore


class TestEpisodic:
    def test_add_and_get_turns(self, tmp_path):
        store = MemoryStore(tmp_path / "memory.sqlite3")
        store.add_turn("s1", "user", "hello")
        store.add_turn("s1", "assistant", "hi there")
        result = store.get_turns("s1")
        assert result["total"] == 2
        assert result["items"][0]["role"] == "user"
        assert result["items"][1]["content"] == "hi there"

    def test_turns_scoped_per_session(self, tmp_path):
        store = MemoryStore(tmp_path / "memory.sqlite3")
        store.add_turn("s1", "user", "a")
        store.add_turn("s2", "user", "b")
        assert store.get_turns("s1")["total"] == 1
        assert store.get_turns("s2")["total"] == 1


class TestSemantic:
    def test_add_and_list_facts(self, tmp_path):
        store = MemoryStore(tmp_path / "memory.sqlite3")
        store.add_fact("session:s1", "likes dark mode", confidence=0.9)
        facts = store.list_facts("session:s1")
        assert len(facts) == 1
        assert facts[0].text == "likes dark mode"

    def test_facts_scoped_per_session(self, tmp_path):
        store = MemoryStore(tmp_path / "memory.sqlite3")
        store.add_fact("session:a", "fact a", confidence=0.9)
        store.add_fact("session:b", "fact b", confidence=0.9)
        assert len(store.list_facts("session:a")) == 1
        assert len(store.list_facts("session:b")) == 1

    def test_version_bumps_on_add(self, tmp_path):
        store = MemoryStore(tmp_path / "memory.sqlite3")
        before = store.version
        store.add_fact("session:s1", "fact", confidence=0.9)
        assert store.version == before + 1
