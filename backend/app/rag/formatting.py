from app.rag.citations import build_sources


def format_context_with_sources(docs: list) -> tuple[str, list[dict]]:
    sources = build_sources(docs)
    parts = []
    for idx, doc in enumerate(docs, start=1):
        source_name = doc.metadata.get("source", "Unknown Source")
        chunk_idx = doc.metadata.get("chunk_index", "")
        header = f"[{idx}] Source: {source_name}"
        if chunk_idx != "":
            header += f" (chunk {chunk_idx})"
        parts.append(f"{header}\n{doc.page_content}")
    return "\n\n---\n\n".join(parts), sources
