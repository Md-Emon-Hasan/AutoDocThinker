import time

_CHARS_PER_TOKEN = 4  # rough estimate, no tokenizer dependency in this codebase


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // _CHARS_PER_TOKEN)


def _score(fact, now: float) -> float:
    age_seconds = max(now - fact.updated_at, 0.0)
    recency = 1.0 / (1.0 + age_seconds / 3600.0)  # decays over hours
    return fact.confidence * recency


def select_facts_within_budget(
    facts: list, token_budget: int, now: float | None = None
) -> list:
    """Rank by confidence*recency, inject only the top slice that fits
    within token_budget. Without this cap, prompts grow unbounded and
    every query gets slower and costlier."""
    now = now if now is not None else time.time()
    ranked = sorted(facts, key=lambda f: _score(f, now), reverse=True)
    selected = []
    used_tokens = 0
    for fact in ranked:
        cost = _estimate_tokens(fact.text)
        if used_tokens + cost > token_budget:
            continue
        selected.append(fact)
        used_tokens += cost
    return selected


def format_memory_section(facts: list) -> str:
    """A clearly delimited section, distinct from retrieved document
    context, so the Verifier does not mistake a remembered fact for a
    cited source. Facts are never assigned a citation id here -- that
    is what makes them structurally non-citable (see
    app/verification/citations.py, which only validates ids against
    build_sources()'s numbering of context_docs)."""
    if not facts:
        return ""
    lines = "\n".join(f"- {fact.text}" for fact in facts)
    return f"\n\n=== REMEMBERED CONTEXT (not a citable document source) ===\n{lines}\n=== END REMEMBERED CONTEXT ===\n"
