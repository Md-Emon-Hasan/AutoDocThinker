import json
import re


def parse_text(output) -> str:
    return str(output).strip()


def parse_json(output: str) -> dict | None:
    """Best-effort strict-JSON parse of an LLM's raw text output.

    Tolerates a fenced ```json ... ``` block or leading/trailing prose
    around the JSON object (common LLM output patterns) but does not
    attempt fuzzy/partial JSON repair. Returns None on failure so callers
    can retry once with a stricter instruction, then degrade.
    """
    text = parse_text(output)
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else text
    if not fenced:
        brace_match = re.search(r"\{.*\}", text, re.DOTALL)
        if brace_match:
            candidate = brace_match.group(0)
    try:
        parsed = json.loads(candidate)
    except (json.JSONDecodeError, TypeError):
        return None
    return parsed if isinstance(parsed, dict) else None
