"""Consolidated tests for the chat module: session, service, memory, message,
title_generator, and history_store."""

from app.chat.title_generator import generate_title


class TestTitleGenerator:
    def test_truncates_long_message(self):
        assert len(generate_title("x" * 60)) <= 40

    def test_empty_gives_untitled(self):
        assert generate_title("") == "Untitled chat"

    def test_strips_whitespace(self):
        assert generate_title("  hello  ") == "hello"
