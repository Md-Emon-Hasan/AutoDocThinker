"""Mechanical (zero-LLM-call) citation and groundedness checks.

Out-of-scope citations and nonexistent citations collapse to the same
check here, since retrieval already enforces scope isolation -- a chunk
outside the caller's scope could never have been retrieved to cite.
"""

import re

_CITATION_PATTERN = re.compile(r"\[(\d+)\]")


def find_citation_ids(answer: str) -> list[int]:
    return [int(match) for match in _CITATION_PATTERN.findall(answer)]


def mechanical_check(answer: str, sources: list[dict]) -> list[str]:
    """Return a list of citation issue descriptions (empty if clean)."""
    issues: list[str] = []
    valid_ids = {source["id"] for source in sources}
    cited_ids = find_citation_ids(answer)

    for cid in cited_ids:
        if cid not in valid_ids:
            issues.append(
                f"citation [{cid}] does not correspond to any retrieved/in-scope "
                "source for this query"
            )

    if answer.strip() and not cited_ids:
        issues.append("answer contains no citations for any claim")

    return issues
