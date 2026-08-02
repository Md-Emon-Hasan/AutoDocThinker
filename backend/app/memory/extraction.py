"""Background fact extraction, run off the request path via FastAPI
BackgroundTasks so the user never waits and failures never break the
conversation. Deliberately sparse -- durable facts only, not every
utterance -- to keep the memory prompt budget small.
"""

import logging

from app.llm.output_parser import parse_json

logger = logging.getLogger(__name__)

_EXTRACTION_INSTRUCTION = (
    "Extract only durable facts or stable preferences about the user from this "
    "conversation turn -- not every statement, only things worth remembering "
    "for future conversations (e.g. their role, stated preferences, ongoing "
    "projects, explicit corrections). If there is nothing durable, return an "
    "empty list.\n\n"
    'Respond with ONLY a JSON object of the exact shape: {"facts": '
    '[{"text": <fact text>, "confidence": <float 0-1>}]}'
)

_CONTRADICTION_INSTRUCTION = (
    "Given a NEW fact and a list of EXISTING facts, identify which existing "
    "fact (if any) the new fact contradicts (e.g. a changed preference, a "
    "corrected detail). Respond with ONLY a JSON object of the exact shape: "
    '{"contradicts_index": <integer index into EXISTING facts, or null>}'
)


def extract_facts(question: str, answer: str, task_client) -> list[dict]:
    """Returns a list of {"text": str, "confidence": float} dicts.
    Never raises -- extraction failure must not fail the conversation."""
    if task_client is None:
        return []
    try:
        turn_text = f"USER: {question}\nASSISTANT: {answer}"
        raw = task_client.answer(turn_text, "", _EXTRACTION_INSTRUCTION)
        parsed = parse_json(raw)
        if parsed is None:
            return []
        facts = parsed.get("facts", [])
        return [
            {"text": str(f["text"]), "confidence": float(f.get("confidence", 0.5))}
            for f in facts
            if isinstance(f, dict) and f.get("text")
        ]
    except Exception:
        logger.exception("Fact extraction failed; conversation is unaffected")
        return []


def run_extraction_job(
    store,
    fact_index,
    task_client,
    scope: str,
    question: str,
    answer: str,
    source_turn: str | None = None,
) -> None:
    """The full background job: extract -> dedupe -> contradiction check
    -> store (+ supersede). Scheduled via BackgroundTasks at the route
    layer; never raises."""
    try:
        facts = extract_facts(question, answer, task_client)
        if not facts:
            return
        existing = store.list_facts(scope)
        existing_texts = {f.text.strip().lower() for f in existing}
        for new_fact in facts:
            normalized = new_fact["text"].strip().lower()
            if normalized in existing_texts:
                continue  # deduplicate against existing facts before writing
            contradicts_idx = detect_contradiction(
                new_fact["text"], existing, task_client
            )
            supersedes_id = (
                existing[contradicts_idx].id if contradicts_idx is not None else None
            )
            stored = store.add_fact(
                scope=scope,
                text=new_fact["text"],
                confidence=new_fact["confidence"],
                source_turn=source_turn,
                supersedes=supersedes_id,
            )
            if fact_index is not None:
                fact_index.add(stored.id, scope, stored.text)
    except Exception:
        logger.exception(
            "Background memory extraction job failed for scope=%s; conversation "
            "already completed and is unaffected",
            scope,
        )


def detect_contradiction(
    new_fact_text: str, existing_facts: list, task_client
) -> int | None:
    """Returns the index into ``existing_facts`` the new fact
    contradicts, or None. A gateway call, run only during background
    extraction -- never on the request path."""
    if task_client is None or not existing_facts:
        return None
    try:
        existing_text = "\n".join(
            f"{i}: {fact.text}" for i, fact in enumerate(existing_facts)
        )
        prompt_context = f"NEW: {new_fact_text}\n\nEXISTING:\n{existing_text}"
        raw = task_client.answer(
            new_fact_text, prompt_context, _CONTRADICTION_INSTRUCTION
        )
        parsed = parse_json(raw)
        if parsed is None:
            return None
        index = parsed.get("contradicts_index")
        if index is None:
            return None
        index = int(index)
        return index if 0 <= index < len(existing_facts) else None
    except Exception:
        logger.exception("Contradiction detection failed; treating as no contradiction")
        return None
