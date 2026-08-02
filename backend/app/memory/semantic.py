from pathlib import Path

import chromadb

from app.core.config import get_config
from app.indexing.embedding_function import HashingEmbeddingFunction


class FactIndex:
    """Separate Chroma collection for semantic-fact embeddings.

    Never mixed into the document index (app/indexing/chroma_store.py) --
    doing so would corrupt document retrieval and citations, and would
    make a fact retrievable as if it were a cited document chunk. Hard
    filtered by scope on every query: a memory leak across sessions is
    the same privacy defect as a document leak.
    """

    def __init__(
        self, persist_directory: Path | str | None = None, cache_manager=None
    ) -> None:
        directory = (
            Path(persist_directory)
            if persist_directory is not None
            else get_config().vector_store_dir
        )
        directory.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(directory))
        embedding_cache = (
            cache_manager.embeddings
            if cache_manager is not None and cache_manager.enabled
            else None
        )
        self._collection = self._client.get_or_create_collection(
            name="memory_facts",
            embedding_function=HashingEmbeddingFunction(cache=embedding_cache),
        )

    def add(self, fact_id: str, scope: str, text: str) -> None:
        self._collection.upsert(
            ids=[fact_id], documents=[text], metadatas=[{"scope": scope}]
        )

    def search(self, scope: str, query: str, k: int = 10) -> list[str]:
        count = self._collection.count()
        if not query or not count:
            return []
        result = self._collection.query(
            query_texts=[query], n_results=min(k, count), where={"scope": scope}
        )
        ids = (result.get("ids") or [[]])[0]
        return list(ids)

    def remove(self, fact_id: str) -> None:
        self._collection.delete(ids=[fact_id])

    def remove_scope(self, scope: str) -> int:
        existing = self._collection.get(where={"scope": scope})
        ids = existing.get("ids") or []
        if ids:
            self._collection.delete(ids=ids)
        return len(ids)
