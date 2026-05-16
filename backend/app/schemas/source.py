from pydantic import BaseModel


class SourceOut(BaseModel):
    id: int
    label: str
