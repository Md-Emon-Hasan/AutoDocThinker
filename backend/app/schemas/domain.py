from pydantic import BaseModel


class DomainOut(BaseModel):
    name: str
    label: str
    description: str
