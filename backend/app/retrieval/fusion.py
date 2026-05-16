from typing import Any


def reciprocal_rank_fusion(groups: list[list[Any]], limit: int) -> list[Any]:
    seen: dict[Any, tuple[Any, float]] = {}
    for docs in groups:
        for rank, doc in enumerate(docs):
            key = doc.metadata.get("chunk_id") or doc.page_content[:100]
            seen[key] = (doc, seen.get(key, (doc, 0.0))[1] + 1.0 / (60 + rank + 1))
    return [
        doc
        for doc, _ in sorted(seen.values(), key=lambda item: item[1], reverse=True)[
            :limit
        ]
    ]
