from fastapi import APIRouter, Depends, HTTPException

from app.api.security import require_admin_token
from app.dependencies import container

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/summary", dependencies=[Depends(require_admin_token)])
def summary():
    box = container()
    return {"domains": box["domains"].names(), "chunks": box["index"].size}


@router.get("/cache/stats", dependencies=[Depends(require_admin_token)])
def cache_stats():
    return container()["cache_manager"].cache_stats()


@router.post("/cache/clear", dependencies=[Depends(require_admin_token)])
def cache_clear(layer: str | None = None):
    manager = container()["cache_manager"]
    if layer:
        try:
            manager.clear_layer(layer)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    else:
        manager.clear_all_caches()
    return {"cleared": layer or "all"}
