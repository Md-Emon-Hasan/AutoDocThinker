from fastapi import APIRouter, HTTPException

from app.dependencies import container
from app.schemas.chat import MessageRequest, SelectProfileRequest, SessionOut
from app.schemas.rag import QueryResponse

router = APIRouter(prefix="/chat/sessions", tags=["chat"])


def _out(session) -> SessionOut:
    return SessionOut(
        session_id=session.id,
        domain=session.domain,
        rag_mode=session.rag_mode,
        history=session.history,
    )


@router.post("", response_model=SessionOut)
def create_session():
    return _out(container()["chat"].create())


@router.get("/{session_id}", response_model=SessionOut)
def get_session(session_id: str):
    try:
        return _out(container()["chat"].get(session_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc


@router.post("/{session_id}/select-profile", response_model=SessionOut)
def select_profile(session_id: str, payload: SelectProfileRequest):
    try:
        return _out(
            container()["chat"].select_profile(
                session_id, payload.domain, payload.rag_mode
            )
        )
    except KeyError as exc:
        message = (
            "Domain not found"
            if str(exc).strip("'") == payload.domain
            else "Session not found"
        )
        raise HTTPException(status_code=404, detail=message) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{session_id}/messages", response_model=QueryResponse)
def message(session_id: str, payload: MessageRequest):
    try:
        return container()["chat"].message(
            session_id, payload.message, payload.metadata_filter
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        msg = str(exc)
        status = 429 if "rate limit" in msg.lower() else 500
        raise HTTPException(status_code=status, detail=msg) from exc
