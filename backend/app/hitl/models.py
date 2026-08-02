from dataclasses import dataclass
from typing import Any


@dataclass
class PendingItem:
    id: str
    kind: str  # e.g. "destructive_index_op", "high_risk_answer", "low_groundedness_answer"
    reason: str
    proposed_output: dict[str, Any]
    scope: str | None
    created_at: float
    status: str = "pending"  # pending | approved | rejected | expired
    decision_reason: str | None = None
    final_output: dict[str, Any] | None = None
    expires_at: float | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "kind": self.kind,
            "reason": self.reason,
            "proposed_output": self.proposed_output,
            "scope": self.scope,
            "created_at": self.created_at,
            "status": self.status,
            "decision_reason": self.decision_reason,
            "final_output": self.final_output,
            "expires_at": self.expires_at,
        }
