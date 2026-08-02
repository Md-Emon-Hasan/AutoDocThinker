from typing import Any

from pydantic import BaseModel


class HITLDecisionRequest(BaseModel):
    reason: str | None = None


class HITLEditRequest(BaseModel):
    edited_output: dict[str, Any]
    reason: str | None = None
