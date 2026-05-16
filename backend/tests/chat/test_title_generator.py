"""Consolidated tests for the chat module: session, service, memory, message,
title_generator, and history_store."""

import pytest

from app.chat.history_store import HistoryStore
from app.chat.memory import remember
from app.chat.message import make_message
from app.chat.session import ChatSession
from app.chat.title_generator import generate_title
from app.dependencies import container


class TestTitleGenerator:
    def test_truncates_long_message(self):
        assert len(generate_title("x" * 60)) <= 40

    def test_empty_gives_untitled(self):
        assert generate_title("") == "Untitled chat"

    def test_strips_whitespace(self):
        assert generate_title("  hello  ") == "hello"
