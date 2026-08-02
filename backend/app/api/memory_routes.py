from fastapi import APIRouter, HTTPException

from app.dependencies import container
from app.schemas.memory import MemoryDeleteOut, MemoryOut

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/{session_id}", response_model=MemoryOut)
def get_memory(session_id: str, limit: int = 50, offset: int = 0):
    box = container()
    memory_store = box.get("memory_store")
    if memory_store is None:
        raise HTTPException(status_code=503, detail="Memory subsystem is disabled")
    episodic = memory_store.get_turns(session_id, limit=limit, offset=offset)
    facts = [f.to_dict() for f in memory_store.list_facts(f"session:{session_id}")]
    return {"episodic": episodic, "facts": facts}


@router.delete("/{session_id}", response_model=MemoryDeleteOut)
def delete_memory(session_id: str):
    """Removes episodic turns and semantic facts, and their embeddings
    from the fact Chroma collection -- a privacy requirement, not a
    convenience."""
    box = container()
    memory_store = box.get("memory_store")
    fact_index = box.get("fact_index")
    if memory_store is None:
        raise HTTPException(status_code=503, detail="Memory subsystem is disabled")
    scope = f"session:{session_id}"
    result = memory_store.delete_session(session_id)
    embeddings_removed = fact_index.remove_scope(scope) if fact_index is not None else 0
    return {
        "session_id": session_id,
        "turns_removed": result["turns_removed"],
        "facts_removed": result["facts_removed"],
        "embeddings_removed": embeddings_removed,
    }
