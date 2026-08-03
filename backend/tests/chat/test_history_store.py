"""Consolidated tests for the chat module: session, service, memory, message,
title_generator, and history_store."""

from app.chat.history_store import HistoryStore


class TestHistoryStore:
    def test_set_and_overwrite(self):
        store = HistoryStore()
        store.set("s1", [{"role": "user", "content": "first"}])
        store.set("s1", [{"role": "user", "content": "second"}])
        assert store._items["s1"][0]["content"] == "second"
