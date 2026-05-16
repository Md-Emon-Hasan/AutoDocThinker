from typing import Any

from pydantic import BaseModel, Field


class SessionOut(BaseModel):
    session_id: str
    domain: str
    rag_mode: str
    history: list[dict[str, str]]


class SelectProfileRequest(BaseModel):
    domain: str
    rag_mode: str


class MessageRequest(BaseModel):
    message: str = Field(min_length=1)
    metadata_filter: dict[str, Any] | None = None
