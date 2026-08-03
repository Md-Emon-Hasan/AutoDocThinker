"""Consolidated tests for the chat module: session, service, memory, message,
title_generator, and history_store."""

from app.chat.session import ChatSession


class TestChatSession:
    def test_session_has_uuid_id(self):
        assert len(ChatSession().id) > 10

    def test_session_defaults(self):
        s = ChatSession()
        assert s.domain == "general"
        assert s.rag_mode == "advanced"
        assert s.history == []

    def test_two_sessions_have_different_ids(self):
        assert ChatSession().id != ChatSession().id
