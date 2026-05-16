from pydantic import BaseModel


class ErrorOut(BaseModel):
    detail: str
