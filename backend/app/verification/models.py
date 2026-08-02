from dataclasses import dataclass, field


@dataclass(frozen=True)
class ClaimSupport:
    text: str
    supported: bool
    chunk_id: str | None = None


@dataclass(frozen=True)
class VerificationResult:
    """Result of a Verifier Agent pass on one generated answer.

    ``verified`` is False when the LLM verification call itself failed or
    degraded (malformed JSON after one retry) -- the answer is still
    returned to the caller, just marked unverified rather than blocking
    question answering. Mechanical citation issues are always populated
    (zero LLM calls), independent of ``verified``.
    """

    groundedness: float | None
    claims: list[ClaimSupport] = field(default_factory=list)
    unsupported_claims: list[str] = field(default_factory=list)
    citation_issues: list[str] = field(default_factory=list)
    verified: bool = False
    regenerated: bool = False

    def to_dict(self) -> dict:
        return {
            "groundedness": self.groundedness,
            "unsupported_claims": list(self.unsupported_claims),
            "citation_issues": list(self.citation_issues),
            "verified": self.verified,
            "regenerated": self.regenerated,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VerificationResult":
        return cls(
            groundedness=data.get("groundedness"),
            unsupported_claims=list(data.get("unsupported_claims", [])),
            citation_issues=list(data.get("citation_issues", [])),
            verified=bool(data.get("verified", False)),
            regenerated=bool(data.get("regenerated", False)),
        )
