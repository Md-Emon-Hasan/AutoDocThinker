from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class ChatSession:
    id: str = field(default_factory=lambda: str(uuid4()))
    domain: str = "general"
    rag_mode: str = "advanced"
    history: list[dict[str, str]] = field(default_factory=list)
