"""SSE event generator for the streaming RAG path.

Mirrors RAGService.query()'s steps but yields an event per step instead
of one monolithic response, reusing RAGService's own helpers rather than
duplicating them. Events are emitted at pipeline-stage granularity (guard
/ cache / dispatch / verify / output guard / HITL), not per LangGraph
node -- true node-level events would require changing the four protected
workflows' `.invoke()` call, which is out of scope.
"""

import time
from typing import Any, Callable, Iterator

from app.rag.modes import ensure_mode
from app.retrieval.filters import scope_filter
from app.workflows.finalize import finalize


def _event(event_type: str, data: dict) -> dict:
    return {"event": event_type, "data": data}


def _ms(start: float) -> float:
    return round((time.time() - start) * 1000, 2)


def _chunk_words(text: str, words_per_chunk: int = 4):
    words = text.split(" ")
    for i in range(0, len(words), words_per_chunk):
        yield " ".join(words[i : i + words_per_chunk]) + (
            " " if i + words_per_chunk < len(words) else ""
        )


def _stream_cached(cached_response: dict) -> Iterator[dict]:
    # A cached answer still streams: cache_hit, then the answer, so the
    # UI behaves consistently whether cached or not.
    yield _event("cache_hit", {})
    for source in cached_response.get("sources", []):
        yield _event("citation", source)
    for chunk in _chunk_words(cached_response["answer"]):
        yield _event("token", {"text": chunk})
    if "verification" in cached_response:
        yield _event("verifier_result", cached_response["verification"])
    yield _event("done", {"response": cached_response})


def _dispatch_and_build_response(
    rag_service, question, clean_mode, profile, history, metadata_filter, scope
) -> Iterator[dict | dict]:
    """Yields progress events, then a final {'_response': ...} marker
    dict carrying (result, response) for the caller to continue with."""
    merged_filter = {
        **profile.metadata_filter,
        **(metadata_filter or {}),
        **scope_filter(scope),
    }
    state = {
        "input": question,
        "domain": profile.name,
        "mode": clean_mode,
        "history": history or [],
        "metadata_filter": merged_filter or None,
        "formatter": rag_service._memory_augmented_formatter(scope, question),
    }
    start = time.time()
    yield _event("node_start", {"node": f"dispatch_{clean_mode}"})
    result = finalize(rag_service._dispatch(clean_mode, state, profile))
    llm_calls = 1
    if clean_mode == "deep":
        budget = result.get("orchestration", {}).get("budget", {})
        llm_calls = budget.get("llm_calls", 1)
        yield _event("budget_status", budget)
    yield _event(
        "retrieval_result", {"candidate_count": len(result.get("context_docs", []))}
    )
    yield _event(
        "node_end",
        {
            "node": f"dispatch_{clean_mode}",
            "duration_ms": _ms(start),
            "llm_calls": llm_calls,
        },
    )
    response = {
        "answer": result["answer"],
        "sources": result.get("sources", []),
        "history": result["history"],
        "mode": clean_mode,
        "domain": profile.name,
        "metadata": {
            key: result[key]
            for key in (
                "confidence",
                "need_retrieval",
                "rewritten_queries",
                "orchestration",
            )
            if key in result
        },
    }
    yield {"_result": result, "_response": response}


def _verify_and_guard(
    rag_service, question, response, result, profile
) -> Iterator[dict]:
    """Verification/output-guard can both rewrite response["answer"]
    (regeneration, blocking) -- tokens must not stream until this
    settles, or the client would show a stale answer that doesn't match
    the eventual `done` event. Yields events; sets response["_blocked"]
    True if the caller should stop and emit `done` immediately."""
    if rag_service.verifier is not None and response["answer"]:
        start = time.time()
        yield _event("node_start", {"node": "verify"})
        rag_service._apply_verification(question, response, result, profile)
        yield _event(
            "node_end", {"node": "verify", "duration_ms": _ms(start), "llm_calls": 1}
        )
        yield _event("verifier_result", response["verification"])

    if rag_service.output_guard is not None and response["answer"]:
        start = time.time()
        yield _event("node_start", {"node": "output_guard"})
        rag_service._apply_output_guard(response, profile.name)
        yield _event(
            "node_end",
            {"node": "output_guard", "duration_ms": _ms(start), "llm_calls": 0},
        )
        if response["governance"]["blocked"]:
            yield _event(
                "guardrail_block",
                {"rules_fired": response["governance"]["rules_fired"]},
            )
            response["_blocked"] = True


def _finalize_and_cache(
    rag_service, response, cache, cache_key, scope, profile
) -> Iterator[dict]:
    """Token stream, HITL check, and answer caching -- the tail of the
    pipeline once verification/output-guard have settled the final
    answer."""
    for source in response["sources"]:
        yield _event("citation", source)
    # No true provider-level token streaming: GroqClient.answer() (used
    # by the four protected workflows' answer node, untouched here)
    # returns the complete text in one call rather than Groq's
    # stream=True deltas. The complete, final (post-verification,
    # post-guard) answer is chunked into words instead, giving the same
    # progressive-rendering UX without requiring those workflows to call
    # a different LLM method.
    for chunk in _chunk_words(response["answer"]):
        yield _event("token", {"text": chunk})

    if rag_service.hitl_gate is not None and response["answer"]:
        pending_response = rag_service._apply_hitl(response, profile.name, scope)
        if pending_response is not None:
            yield _event("hitl_required", pending_response["hitl"])
            yield _event("done", {"response": pending_response})
            return

    if cache is not None and response["answer"]:
        to_cache: dict[str, Any] = {
            "answer": response["answer"],
            "sources": response["sources"],
            "metadata": response["metadata"],
        }
        if "verification" in response:
            to_cache["verification"] = response["verification"]
        cache.set(cache_key, to_cache)

    yield _event("done", {"response": response})


def stream_query(
    rag_service,
    question: str,
    domain: str,
    mode: str,
    history: list | None,
    metadata_filter: dict | None,
    scope: str | None,
    is_cancelled: Callable[[], bool],
) -> Iterator[dict]:
    clean_mode = ensure_mode(mode)
    profile = rag_service.domains.get(domain)

    # -- input guard -------------------------------------------------
    start = time.time()
    yield _event("node_start", {"node": "input_guard"})
    question, blocked = rag_service._check_input_guard(
        question, clean_mode, profile, history, scope
    )
    yield _event(
        "node_end", {"node": "input_guard", "duration_ms": _ms(start), "llm_calls": 0}
    )
    if blocked is not None:
        yield _event(
            "guardrail_block",
            {"rules_fired": blocked.get("governance", {}).get("rules_fired", [])},
        )
        yield _event("done", {"response": blocked})
        return
    if is_cancelled():
        yield _event("error", {"message": "client disconnected"})
        return

    # -- cache lookup --------------------------------------------------
    start = time.time()
    yield _event("node_start", {"node": "cache_lookup"})
    cache, cache_key, cached_response = rag_service._check_cache(
        question, clean_mode, profile, scope, history
    )
    yield _event(
        "node_end", {"node": "cache_lookup", "duration_ms": _ms(start), "llm_calls": 0}
    )
    if cached_response is not None:
        yield from _stream_cached(cached_response)
        return
    if is_cancelled():
        yield _event("error", {"message": "client disconnected"})
        return

    # -- mode dispatch (naive/advanced/crag/self_rag/deep) --------------
    result = response = None
    for item in _dispatch_and_build_response(
        rag_service, question, clean_mode, profile, history, metadata_filter, scope
    ):
        if "_response" in item:
            result, response = item["_result"], item["_response"]
        else:
            yield item
    if is_cancelled():
        yield _event("error", {"message": "client disconnected"})
        return

    yield from _verify_and_guard(rag_service, question, response, result, profile)
    if response.get("_blocked"):
        yield _event("done", {"response": response})
        return

    yield from _finalize_and_cache(
        rag_service, response, cache, cache_key, scope, profile
    )
