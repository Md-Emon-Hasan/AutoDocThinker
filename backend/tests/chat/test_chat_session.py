"""Consolidated tests for the chat module: session, service, memory, message,
title_generator, and history_store."""

import pytest

from app.chat.history_store import HistoryStore
from app.chat.memory import remember
from app.chat.message import make_message
from app.chat.session import ChatSession
from app.chat.title_generator import generate_title
from app.dependencies import container


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
