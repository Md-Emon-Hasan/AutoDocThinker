"""Consolidated tests for the chat module: session, service, memory, message,
title_generator, and history_store."""

import pytest

from app.chat.history_store import HistoryStore
from app.chat.memory import remember
from app.chat.message import make_message
from app.chat.session import ChatSession
from app.chat.title_generator import generate_title
from app.dependencies import container


class TestHistoryStore:
    def test_set_and_overwrite(self):
        store = HistoryStore()
        store.set("s1", [{"role": "user", "content": "first"}])
        store.set("s1", [{"role": "user", "content": "second"}])
        assert store._items["s1"][0]["content"] == "second"
