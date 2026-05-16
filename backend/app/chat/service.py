from typing import Any, cast

from app.chat.session import ChatSession
from app.rag.modes import ensure_mode


class ChatService:
    def __init__(self, rag_service) -> None:
        self.rag_service = rag_service
        self.sessions: dict[str, ChatSession] = {}

    def create(self) -> ChatSession:
        session = ChatSession()
        self.sessions[session.id] = session
        return session

    def get(self, session_id: str) -> ChatSession:
        if session_id not in self.sessions:
            raise KeyError(session_id)
        return self.sessions[session_id]

    def select_profile(
        self, session_id: str, domain: str, rag_mode: str
    ) -> ChatSession:
        session = self.get(session_id)
        self.rag_service.domains.get(domain)
        ensure_mode(rag_mode)
        session.domain = domain
        session.rag_mode = rag_mode
        return session

    def message(
        self, session_id: str, message: str, metadata_filter=None
    ) -> dict[str, Any]:
        session = self.get(session_id)
        result = self.rag_service.query(
            message, session.domain, session.rag_mode, session.history, metadata_filter
        )
        session.history = result["history"]
        return cast(dict[str, Any], result)
