"""Consolidated tests for the chat module: session, service, memory, message,
title_generator, and history_store."""

from app.chat.message import make_message


class TestMakeMessage:
    def test_returns_dict(self):
        assert make_message("user", "hi") == {"role": "user", "content": "hi"}
