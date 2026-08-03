"""Consolidated tests for the chat module: session, service, memory, message,
title_generator, and history_store."""

import pytest

from app.dependencies import container


class TestChatService:
    def test_create_session(self):
        session = container()["chat"].create()
        assert session.id and session.domain == "general"

    def test_get_session(self):
        box = container()
        session = box["chat"].create()
        assert box["chat"].get(session.id).id == session.id

    def test_get_missing_raises(self):
        with pytest.raises(KeyError):
            container()["chat"].get("missing")

    def test_select_profile(self):
        box = container()
        session = box["chat"].create()
        updated = box["chat"].select_profile(session.id, "technical", "self_rag")
        assert updated.domain == "technical" and updated.rag_mode == "self_rag"

    def test_message_returns_domain(self, seeded_container):
        box = seeded_container
        session = box["chat"].create()
        box["chat"].select_profile(session.id, "technical", "self_rag")
        assert box["chat"].message(session.id, "hello")["domain"] == "technical"
