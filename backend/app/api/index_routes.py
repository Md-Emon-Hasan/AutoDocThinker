from fastapi import APIRouter, Depends, HTTPException

from app.api.security import require_admin_token
from app.dependencies import container

router = APIRouter(prefix="/index", tags=["index"])


@router.get("/status")
def status():
    box = container()
    index = box["index"]
    dense_index = box["dense_index"]
    return {
        "total_chunks": index.size,
        "sources": index.sources,
        "source_details": index.source_details,
        # Additive: per-scope, per-index-type counts so isolation is
        # observable rather than assumed.
        "index_version": index.version,
        "scope_counts": {
            "dense": dense_index.scope_counts,
            "bm25": index.scope_counts,
        },
    }


def _gate_or_none(kind: str, reason: str, proposed_output: dict) -> dict | None:
    """If HITL is configured to gate destructive index ops, create a
    pending item and return its dict; otherwise return None so the
    caller executes immediately (HITL is off by default)."""
    box = container()
    gate = box.get("hitl_gate")
    if gate is not None and gate.should_gate_destructive_op():
        pending = gate.create_pending(kind, reason, proposed_output, scope=None)
        box["audit_log"].record(None, kind, "gated_pending")
        return {"pending": True, "pending_id": pending["id"], "kind": kind}
    return None


@router.delete("/source/{source_id}", dependencies=[Depends(require_admin_token)])
def remove_source(source_id: str):
    box = container()
    gated = _gate_or_none(
        "remove_source", "destructive index op", {"source_id": source_id}
    )
    if gated is not None:
        return gated
    removed = box["index"].remove_source(source_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Source not found in index")
    box["dense_index"].remove_source(source_id)
    return {"removed": True, "source_id": source_id}


@router.delete("/scope/{scope:path}", dependencies=[Depends(require_admin_token)])
def remove_scope(scope: str):
    """Remove every chunk belonging to ``scope`` from both indices.

    This is the session-lifecycle deletion path: removing a chat
    session's data doesn't require knowing its individual source ids.
    """
    box = container()
    gated = _gate_or_none("remove_scope", "destructive index op", {"scope": scope})
    if gated is not None:
        return gated
    bm25_removed = box["index"].remove_scope(scope)
    dense_removed = box["dense_index"].remove_scope(scope)
    if not bm25_removed and not dense_removed:
        raise HTTPException(status_code=404, detail="Scope not found in index")
    return {
        "removed": True,
        "scope": scope,
        "bm25_chunks_removed": bm25_removed,
        "dense_chunks_removed": dense_removed,
    }


@router.delete("", dependencies=[Depends(require_admin_token)])
def clear_index():
    box = container()
    gated = _gate_or_none("clear_index", "destructive index op", {})
    if gated is not None:
        return gated
    box["index"].clear()
    box["dense_index"].clear()
    return {"cleared": True}
