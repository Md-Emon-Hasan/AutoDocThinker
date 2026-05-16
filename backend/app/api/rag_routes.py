from fastapi import APIRouter, HTTPException

from app.dependencies import container
from app.rag.modes import RAG_MODES
from app.schemas.rag import QueryRequest, QueryResponse

router = APIRouter(tags=["rag"])


@router.get("/rag-modes")
def rag_modes():
    return {"modes": list(RAG_MODES)}


@router.get("/rag-profiles")
def rag_profiles():
    return [
        {"domain": domain.name, "rag_modes": list(RAG_MODES)}
        for domain in container()["domains"].list()
    ]


@router.post("/rag/query", response_model=QueryResponse)
def query(payload: QueryRequest):
    try:
        return container()["rag"].query(
            payload.question,
            payload.domain,
            payload.rag_mode,
            payload.history,
            payload.metadata_filter,
        )
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        msg = str(exc)
        status = 429 if "rate limit" in msg.lower() else 500
        raise HTTPException(status_code=status, detail=msg) from exc
