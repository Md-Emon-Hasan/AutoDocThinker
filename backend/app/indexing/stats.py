def index_stats(index) -> dict:
    return {"total_chunks": index.size, "source_count": len(index.sources)}
