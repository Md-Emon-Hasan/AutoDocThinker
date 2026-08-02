"""Config-driven HITL gating, off by default.

Gates post-generation (same boundary the Verifier uses) rather than
mid-workflow, since the four protected workflows have no interrupt()
points and adding one would mean restructuring their graphs.
"""

from app.governance.policy import is_high_risk
from app.hitl.store import HITLStore


class HITLGate:
    def __init__(self, store: HITLStore, config) -> None:
        self.store = store
        self.config = config

    @property
    def enabled(self) -> bool:
        return bool(self.config.hitl_enabled)

    def should_gate_destructive_op(self) -> bool:
        return self.enabled and self.config.hitl_gate_destructive_ops

    def should_gate_answer(
        self, domain: str, verification: dict | None
    ) -> tuple[bool, str | None]:
        if not self.enabled:
            return False, None
        groundedness = (verification or {}).get("groundedness")
        below_threshold = (
            groundedness is not None
            and groundedness < self.config.verification_min_groundedness
        )
        if self.config.hitl_gate_low_groundedness and below_threshold:
            return True, "low_groundedness_answer"
        if (
            self.config.hitl_gate_high_risk_domains
            and is_high_risk(domain)
            and below_threshold
        ):
            return True, "high_risk_low_confidence_answer"
        return False, None

    def create_pending(
        self, kind: str, reason: str, proposed_output: dict, scope
    ) -> dict:
        item = self.store.create(
            kind=kind,
            reason=reason,
            proposed_output=proposed_output,
            scope=scope,
            ttl_seconds=self.config.hitl_expiry_seconds,
        )
        return item.to_dict()
