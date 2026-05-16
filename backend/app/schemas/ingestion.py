from pydantic import BaseModel


class IngestRequest(BaseModel):
    source: str
    file_type: str


class IngestTextRequest(BaseModel):
    text: str
    title: str = "pasted_text"


class IngestResponse(BaseModel):
    chunks_added: int
    total_chunks: int
    sources: list[str]
