from fastapi import APIRouter, Depends, HTTPException

from app.api.security import require_admin_token
from app.dependencies import container
from app.schemas.hitl import HITLDecisionRequest, HITLEditRequest

router = APIRouter(prefix="/hitl", tags=["hitl"])

_DESTRUCTIVE_KINDS = {"remove_source", "remove_scope", "clear_index"}
_DEFAULT_DECISION = HITLDecisionRequest()


def _execute_approved_destructive_op(kind: str, proposed_output: dict) -> None:
    """Perform the actual index mutation an approved destructive-op
    pending item describes -- execution logic lives in the route layer
    (which already has container() access), not the data-only gate/store."""
    box = container()
    if kind == "remove_source":
        box["index"].remove_source(proposed_output["source_id"])
        box["dense_index"].remove_source(proposed_output["source_id"])
    elif kind == "remove_scope":
        box["index"].remove_scope(proposed_output["scope"])
        box["dense_index"].remove_scope(proposed_output["scope"])
    elif kind == "clear_index":
        box["index"].clear()
        box["dense_index"].clear()


@router.get("/pending", dependencies=[Depends(require_admin_token)])
def list_pending(limit: int = 50, offset: int = 0):
    return container()["hitl_store"].list_pending(limit=limit, offset=offset)


@router.post("/{item_id}/approve", dependencies=[Depends(require_admin_token)])
def approve(item_id: str, payload: HITLDecisionRequest = _DEFAULT_DECISION):
    box = container()
    item = box["hitl_store"].approve(item_id, reason=payload.reason)
    if item is None:
        raise HTTPException(status_code=404, detail="Pending item not found")
    if item.kind in _DESTRUCTIVE_KINDS:
        _execute_approved_destructive_op(item.kind, item.proposed_output)
    box["audit_log"].record(item.scope, item.kind, "approved", payload.reason or "")
    return item.to_dict()


@router.post("/{item_id}/reject", dependencies=[Depends(require_admin_token)])
def reject(item_id: str, payload: HITLDecisionRequest = _DEFAULT_DECISION):
    box = container()
    item = box["hitl_store"].reject(item_id, reason=payload.reason)
    if item is None:
        raise HTTPException(status_code=404, detail="Pending item not found")
    box["audit_log"].record(item.scope, item.kind, "rejected", payload.reason or "")
    return item.to_dict()


@router.post("/{item_id}/edit", dependencies=[Depends(require_admin_token)])
def edit(item_id: str, payload: HITLEditRequest):
    box = container()
    item = box["hitl_store"].edit_and_approve(
        item_id, payload.edited_output, reason=payload.reason
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Pending item not found")
    box["audit_log"].record(
        item.scope, item.kind, "edited_and_approved", payload.reason or ""
    )
    return item.to_dict()
