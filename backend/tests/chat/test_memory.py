"""Consolidated tests for the chat module: session, service, memory, message,
title_generator, and history_store."""

import pytest

from app.chat.history_store import HistoryStore
from app.chat.memory import remember
from app.chat.message import make_message
from app.chat.session import ChatSession
from app.chat.title_generator import generate_title
from app.dependencies import container


class TestMemory:
    def test_remember_appends(self):
        result = remember([{"role": "user", "content": "hi"}], "assistant", "hello")
        assert len(result) == 2
        assert result[-1] == {"role": "assistant", "content": "hello"}

    def test_remember_empty(self):
        assert len(remember([], "user", "first")) == 1
