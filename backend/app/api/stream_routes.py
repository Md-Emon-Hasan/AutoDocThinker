"""SSE streaming endpoint.

Frontend uses fetch + ReadableStream (see frontend/src/api.js), not
EventSource, since EventSource can't POST the query payload.
"""

import json
import queue
import threading

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.dependencies import container
from app.memory.extraction import run_extraction_job
from app.rag.streaming import stream_query
from app.schemas.chat import MessageRequest
from app.schemas.rag import QueryRequest

router = APIRouter(tags=["streaming"])

_KEEPALIVE_SECONDS = 15
_SENTINEL = object()
_SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}


def _format_sse(event: dict) -> str:
    return f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"


def _event_error(message: str) -> dict:
    return {"event": "error", "data": {"message": message}}


def _run_with_keepalive(generator, keepalive_seconds: float):
    """Bridges a plain (possibly slow-to-yield) generator onto a queue
    consumed with a timeout, so a keepalive comment can be emitted
    during long silent gaps (e.g. a slow `deep` query) without blocking
    the whole response on the next real event.
    """
    q: queue.Queue = queue.Queue()

    def produce():
        try:
            for item in generator:
                q.put(item)
        except Exception as exc:  # noqa: BLE001 - surfaced as an SSE error event
            q.put(_event_error(str(exc)))
        finally:
            q.put(_SENTINEL)

    thread = threading.Thread(target=produce, daemon=True)
    thread.start()

    while True:
        try:
            item = q.get(timeout=keepalive_seconds)
        except queue.Empty:
            yield ": keepalive\n\n"
            continue
        if item is _SENTINEL:
            return
        yield _format_sse(item)


def _sse_response(
    generator, request: Request, cancel_event: threading.Event
) -> StreamingResponse:
    async def event_source():
        for chunk in _run_with_keepalive(generator, _KEEPALIVE_SECONDS):
            if await request.is_disconnected():
                # Cancel the workflow -- an abandoned request must not
                # keep burning LLM calls/budget. stream_query() checks
                # is_cancelled() between pipeline stages and stops early.
                cancel_event.set()
                return
            yield chunk

    return StreamingResponse(
        event_source(), media_type="text/event-stream", headers=_SSE_HEADERS
    )


@router.post("/rag/stream")
async def stream_rag_query(payload: QueryRequest, request: Request):
    box = container()
    cancel_event = threading.Event()
    generator = stream_query(
        box["rag"],
        payload.question,
        payload.domain,
        payload.rag_mode,
        payload.history,
        payload.metadata_filter,
        payload.scope,
        cancel_event.is_set,
    )
    return _sse_response(generator, request, cancel_event)


def _persist_session_turn(
    box, session, session_id, scope, message, background_tasks, response
):
    """Mirrors ChatService.message()'s post-response bookkeeping (history
    persistence, background fact extraction scheduling) for the
    streaming session endpoint's `done` event."""
    if "history" not in response:
        return
    session.history = response["history"]
    if box["chat"].history_store is not None:
        box["chat"].history_store.set(session_id, session.history)
    memory_store = box.get("memory_store")
    if memory_store is not None and response.get("answer"):
        background_tasks.add_task(
            run_extraction_job,
            memory_store,
            box.get("fact_index"),
            box.get("memory_extraction_client"),
            scope,
            message,
            response["answer"],
        )


def _tap_done_event(generator, on_done):
    for event in generator:
        if event["event"] == "done":
            on_done(event["data"].get("response", {}))
        yield event


@router.post("/chat/sessions/{session_id}/messages/stream")
async def stream_chat_message(
    session_id: str,
    payload: MessageRequest,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """Session-scoped counterpart to /rag/stream, mirroring
    ChatService.message()'s behaviour but streamed."""
    box = container()
    try:
        session = box["chat"].get(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc

    cancel_event = threading.Event()
    scope = f"session:{session.id}"
    generator = stream_query(
        box["rag"],
        payload.message,
        session.domain,
        session.rag_mode,
        session.history,
        payload.metadata_filter,
        scope,
        cancel_event.is_set,
    )
    tapped = _tap_done_event(
        generator,
        lambda response: _persist_session_turn(
            box, session, session_id, scope, payload.message, background_tasks, response
        ),
    )
    return _sse_response(tapped, request, cancel_event)
