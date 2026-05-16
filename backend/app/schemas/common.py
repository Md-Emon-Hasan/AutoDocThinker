from pydantic import BaseModel


class MessageOut(BaseModel):
    message: str
