import logging

from app.verification.citations import mechanical_check
from app.verification.critic import Critic
from app.verification.models import ClaimSupport, VerificationResult

logger = logging.getLogger(__name__)


class VerifierAgent:
    """Groundedness + hallucination detection + citation validation.

    One agent, not three: "is the answer supported" and "is it
    hallucinated" are the same check inverted, and citation validation is
    its mechanical half. task_client is a gateway client bound to
    TaskCategory.VERIFICATION (None disables the LLM half, mechanical
    checks still run).
    """

    def __init__(self, task_client=None, critic: Critic | None = None) -> None:
        self.task_client = task_client
        self.critic = critic or Critic()

    def verify(
        self, question: str, answer: str, context: str, sources: list[dict]
    ) -> VerificationResult:
        citation_issues = mechanical_check(answer, sources)

        if self.task_client is None or not answer.strip():
            return VerificationResult(
                groundedness=None, citation_issues=citation_issues, verified=False
            )

        try:
            parsed = self.critic.assess(question, answer, context, self.task_client)
        except Exception:
            logger.exception("Verifier: critic call failed, marking unverified")
            parsed = None

        if parsed is None:
            return VerificationResult(
                groundedness=None, citation_issues=citation_issues, verified=False
            )

        claims = [
            ClaimSupport(
                text=str(c.get("text", "")),
                supported=bool(c.get("supported", False)),
                chunk_id=c.get("chunk_id"),
            )
            for c in parsed.get("claims", [])
            if isinstance(c, dict)
        ]
        groundedness = parsed.get("groundedness")
        try:
            groundedness = float(groundedness) if groundedness is not None else None
        except (TypeError, ValueError):
            groundedness = None

        return VerificationResult(
            groundedness=groundedness,
            claims=claims,
            unsupported_claims=[str(c) for c in parsed.get("unsupported_claims", [])],
            citation_issues=citation_issues,
            verified=True,
        )
