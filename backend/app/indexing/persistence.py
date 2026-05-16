def snapshot_index(index) -> dict:
    return {"total_chunks": index.size, "sources": index.sources}
