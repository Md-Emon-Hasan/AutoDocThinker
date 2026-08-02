from pathlib import Path
from uuid import uuid4

import chromadb

from app.core.config import get_config
from app.indexing.embedding_function import HashingEmbeddingFunction
from app.ingestion.document import Document

DEFAULT_SCOPE = "shared"


class ChromaStore:
    """Real, persistent dense vector store backed by ChromaDB.

    One collection per domain (``docs_<domain>``); scope isolation across
    sessions further subdivides *within* a domain's collection via metadata
    (see Stage 2), rather than via more collections, which would make
    cross-scope admin queries harder.
    """

    def __init__(
        self,
        domain: str = "general",
        persist_directory: Path | str | None = None,
        cache_manager=None,
    ) -> None:
        self.domain = domain
        self.persisted = False
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
            name=f"docs_{domain}",
            embedding_function=HashingEmbeddingFunction(cache=embedding_cache),
        )

    def add(self, chunks: list) -> int:
        if not chunks:
            return 0
        ids, documents, metadatas = [], [], []
        for chunk in chunks:
            chunk.metadata.setdefault("scope", DEFAULT_SCOPE)
            chunk_id = chunk.metadata.get("chunk_id") or str(uuid4())
            chunk.metadata["chunk_id"] = chunk_id
            ids.append(chunk_id)
            documents.append(chunk.page_content)
            metadatas.append(
                {key: val for key, val in chunk.metadata.items() if val is not None}
            )
        self._collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        return len(chunks)

    def search(
        self, query: str, k: int = 8, metadata_filter: dict | None = None
    ) -> list:
        count = self._collection.count()
        if not query or not count:
            return []
        result = self._collection.query(
            query_texts=[query],
            n_results=min(k, count),
            where=self._build_where(metadata_filter),
        )
        docs = (result.get("documents") or [[]])[0]
        metas = (result.get("metadatas") or [[]])[0]
        return [Document(text, dict(meta or {})) for text, meta in zip(docs, metas)]

    def remove_source(self, source_id: str) -> bool:
        existing = self._collection.get(where={"source_id": source_id})
        ids = existing.get("ids") or []
        if not ids:
            return False
        self._collection.delete(ids=ids)
        return True

    def remove_scope(self, scope: str) -> int:
        existing = self._collection.get(where={"scope": scope})
        ids = existing.get("ids") or []
        if ids:
            self._collection.delete(ids=ids)
        return len(ids)

    def clear(self) -> None:
        existing = self._collection.get()
        ids = existing.get("ids") or []
        if ids:
            self._collection.delete(ids=ids)

    def persist(self) -> bool:
        self.persisted = True
        return self.persisted

    @property
    def scope_counts(self) -> dict[str, int]:
        existing = self._collection.get()
        metadatas = existing.get("metadatas") or []
        counts: dict[str, int] = {}
        for meta in metadatas:
            scope = (meta or {}).get("scope", DEFAULT_SCOPE)
            counts[scope] = counts.get(scope, 0) + 1
        return counts

    @staticmethod
    def _condition(key: str, val) -> dict:
        if isinstance(val, (list, tuple, set)):
            return {key: {"$in": list(val)}}
        return {key: val}

    @classmethod
    def _build_where(cls, metadata_filter: dict | None) -> dict | None:
        if not metadata_filter:
            return None
        if len(metadata_filter) == 1:
            ((key, val),) = metadata_filter.items()
            return cls._condition(key, val)
        return {
            "$and": [cls._condition(key, val) for key, val in metadata_filter.items()]
        }
