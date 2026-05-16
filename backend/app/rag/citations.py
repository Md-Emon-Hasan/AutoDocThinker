def source_label(metadata: dict) -> str:
    source = metadata.get("source") or "unknown"
    page = metadata.get("page")
    return f"{source} p.{page}" if page is not None else str(source)


def format_source_label(meta: dict) -> str:
    return source_label(meta)


def build_sources(docs: list) -> list[dict]:
    sources = []
    for idx, doc in enumerate(docs, start=1):
        meta = doc.metadata
        sources.append(
            {
                "id": idx,
                "label": source_label(meta),
                "source": meta.get("source"),
                "chunk_id": meta.get("chunk_id"),
            }
        )
    return sources
