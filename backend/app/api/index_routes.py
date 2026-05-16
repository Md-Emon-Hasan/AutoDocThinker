from fastapi import APIRouter, HTTPException

from app.dependencies import container

router = APIRouter(prefix="/index", tags=["index"])


@router.get("/status")
def status():
    index = container()["index"]
    return {
        "total_chunks": index.size,
        "sources": index.sources,
        "source_details": index.source_details,
    }


@router.delete("/source/{source_id}")
def remove_source(source_id: str):
    removed = container()["index"].remove_source(source_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Source not found in index")
    return {"removed": True, "source_id": source_id}


@router.delete("")
def clear_index():
    container()["index"].clear()
    return {"cleared": True}
