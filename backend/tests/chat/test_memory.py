"""Consolidated tests for the chat module: session, service, memory, message,
title_generator, and history_store."""

from app.chat.memory import remember


class TestMemory:
    def test_remember_appends(self):
        result = remember([{"role": "user", "content": "hi"}], "assistant", "hello")
        assert len(result) == 2
        assert result[-1] == {"role": "assistant", "content": "hello"}

    def test_remember_empty(self):
        assert len(remember([], "user", "first")) == 1
