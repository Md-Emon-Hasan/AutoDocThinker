from typing import Any, cast


def vector_search(index, query: str, k: int, metadata_filter=None) -> list[Any]:
    return cast(list[Any], index.search(query, k, metadata_filter))
