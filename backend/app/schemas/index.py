from pydantic import BaseModel


class IndexStatusOut(BaseModel):
    total_chunks: int
    sources: list[str]
