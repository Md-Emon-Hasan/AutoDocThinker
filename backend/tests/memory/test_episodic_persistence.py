"""Episodic turns survive a restart; app/chat/history_store.py's public
interface is unchanged whether or not a memory_store is supplied."""

from app.chat.history_store import HistoryStore
from app.memory.store import MemoryStore


class TestEpisodicPersistence:
    def test_turns_survive_reopen(self, tmp_path):
        db_path = tmp_path / "memory.sqlite3"
        store = MemoryStore(db_path)
        store.add_turn("s1", "user", "hello")

        reopened = MemoryStore(db_path)
        assert reopened.get_turns("s1")["total"] == 1

    def test_history_store_interface_unchanged_without_memory_store(self):
        """The exact pre-Stage-5 test behaviour: set()/_items only,
        no memory_store required."""
        store = HistoryStore()
        store.set("s1", [{"role": "user", "content": "first"}])
        store.set("s1", [{"role": "user", "content": "second"}])
        assert store._items["s1"][0]["content"] == "second"

    def test_history_store_persists_new_turns_when_backed(self, tmp_path):
        memory_store = MemoryStore(tmp_path / "memory.sqlite3")
        store = HistoryStore(memory_store=memory_store)
        store.set("s1", [{"role": "user", "content": "first"}])
        store.set(
            "s1",
            [
                {"role": "user", "content": "first"},
                {"role": "assistant", "content": "reply"},
            ],
        )
        persisted = memory_store.get_turns("s1")
        assert persisted["total"] == 2

    def test_history_store_get_falls_back_to_memory_store(self, tmp_path):
        db_path = tmp_path / "memory.sqlite3"
        memory_store = MemoryStore(db_path)
        memory_store.add_turn("s1", "user", "hello")

        # A fresh HistoryStore (simulating a restart) has no in-process
        # cache yet, but get() must still surface durable history.
        fresh_store = HistoryStore(memory_store=memory_store)
        history = fresh_store.get("s1")
        assert history == [{"role": "user", "content": "hello"}]

    def test_history_store_get_without_memory_store_returns_empty_for_unknown(self):
        store = HistoryStore()
        assert store.get("unknown") == []
