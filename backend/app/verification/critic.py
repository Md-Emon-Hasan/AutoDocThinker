"""The one shared reflection/critique implementation, used by the
Verifier Agent. Self-RAG's old self_rag_critique/self_rag_revise stubs
never had real logic to consolidate from, so they're left untouched.
"""

import logging

from app.llm.output_parser import parse_json

logger = logging.getLogger(__name__)

_JSON_INSTRUCTION = (
    "You are a strict fact-checking critic. Given a QUESTION, the RETRIEVED "
    "CONTEXT, and a candidate ANSWER, judge whether each claim in the answer "
    "is supported by the context.\n\n"
    "Respond with ONLY a JSON object (no prose, no markdown fences) of the "
    'exact shape: {"groundedness": <float 0-1>, "claims": '
    '[{"text": <claim text>, "supported": <true|false>, '
    '"chunk_id": <supporting chunk id or null>}], '
    '"unsupported_claims": [<claim text>, ...]}'
)

_STRICT_RETRY_SUFFIX = (
    "\n\nYour previous response was not valid JSON. Respond again with ONLY "
    "the JSON object described above -- no other text."
)


class Critic:
    """One reusable critique step: LLM call -> structured JSON verdict."""

    def assess(self, question: str, answer: str, context: str, task_client) -> dict:
        """Return a parsed dict per _JSON_INSTRUCTION's shape, or None on
        failure after one stricter retry."""
        payload_context = (
            f"RETRIEVED CONTEXT:\n{context}\n\nCANDIDATE ANSWER:\n{answer}"
        )
        raw = task_client.answer(question, payload_context, _JSON_INSTRUCTION)
        parsed = parse_json(raw)
        if parsed is not None:
            return parsed

        logger.warning("Critic: malformed JSON on first attempt, retrying once")
        raw_retry = task_client.answer(
            question, payload_context, _JSON_INSTRUCTION + _STRICT_RETRY_SUFFIX
        )
        parsed_retry = parse_json(raw_retry)
        if parsed_retry is None:
            logger.warning("Critic: malformed JSON after retry, degrading")
        return parsed_retry
