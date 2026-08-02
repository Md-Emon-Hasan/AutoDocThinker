from pydantic import BaseModel


class IngestRequest(BaseModel):
    source: str
    file_type: str
    scope: str | None = None


class IngestTextRequest(BaseModel):
    text: str
    title: str = "pasted_text"
    scope: str | None = None


class IngestResponse(BaseModel):
    chunks_added: int
    total_chunks: int
    sources: list[str]
    scope: str | None = None
