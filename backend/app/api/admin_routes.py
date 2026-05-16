from fastapi import APIRouter

from app.dependencies import container

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/summary")
def summary():
    box = container()
    return {"domains": box["domains"].names(), "chunks": box["index"].size}
