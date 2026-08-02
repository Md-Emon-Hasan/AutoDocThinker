import re
from dataclasses import dataclass, field

from app.governance.input_guard import detect_pii, redact_pii
from app.governance.policy import get_policy, is_high_risk

_DISCLAIMER_MARKERS = re.compile(
    r"(not (legal|medical|financial) advice|consult a (lawyer|attorney|doctor|"
    r"physician|financial advisor)|for informational purposes only)",
    re.I,
)
_HEDGE_MARKERS = re.compile(
    r"\b(may|might|could|generally|typically|in most cases)\b", re.I
)


@dataclass
class OutputGuardResult:
    allowed: bool
    rules_fired: list[str] = field(default_factory=list)
    redacted_text: str | None = None
    warning: str | None = None


class OutputGuard:
    """Output guard: consumes the Stage 3 verifier result rather than
    making its own LLM call for groundedness. Fails closed for high-risk
    domains, open-with-warning for General. A guard crash never becomes
    a 500 -- it degrades to the domain's configured fail mode.
    """

    def check(
        self, answer: str, domain: str, verification: dict | None = None
    ) -> OutputGuardResult:
        try:
            return self._check(answer, domain, verification)
        except Exception:
            if is_high_risk(domain):
                return OutputGuardResult(allowed=False, rules_fired=["guard_error"])
            return OutputGuardResult(
                allowed=True,
                rules_fired=["guard_error"],
                warning="Output guard failed; allowed with warning (non-high-risk domain).",
            )

    def _check(
        self, answer: str, domain: str, verification: dict | None
    ) -> OutputGuardResult:
        policy = get_policy(domain)
        rules_fired: list[str] = []
        redacted_text = None

        if detect_pii(answer):
            rules_fired.append("pii_leakage")
            redacted_text = redact_pii(answer)

        groundedness = (verification or {}).get("groundedness")
        ungrounded = (
            groundedness is not None and groundedness < policy["min_groundedness"]
        )
        if ungrounded:
            rules_fired.append("ungrounded_assertion")

        missing_disclaimer = False
        if (
            policy["require_disclaimer"]
            and not _DISCLAIMER_MARKERS.search(answer)
            and not _HEDGE_MARKERS.search(answer)
        ):
            rules_fired.append("missing_disclaimer_or_hedging")
            missing_disclaimer = True

        blocking = ungrounded or missing_disclaimer
        if blocking and policy["fail_closed"]:
            return OutputGuardResult(
                allowed=False, rules_fired=rules_fired, redacted_text=redacted_text
            )
        if blocking:
            return OutputGuardResult(
                allowed=True,
                rules_fired=rules_fired,
                redacted_text=redacted_text,
                warning="Output flagged by governance but allowed (non-high-risk domain).",
            )
        return OutputGuardResult(
            allowed=True, rules_fired=rules_fired, redacted_text=redacted_text
        )
