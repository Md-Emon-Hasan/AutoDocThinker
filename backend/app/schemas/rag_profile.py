from pydantic import BaseModel


class RAGProfileOut(BaseModel):
    domain: str
    rag_modes: list[str]
