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
        self._collection = self._client.get_or_create_collection(
            name=f"docs_{domain}",
            embedding_function=HashingEmbeddingFunction(),
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

    def clear(self) -> None:
        existing = self._collection.get()
        ids = existing.get("ids") or []
        if ids:
            self._collection.delete(ids=ids)

    def persist(self) -> bool:
        self.persisted = True
        return self.persisted

    @staticmethod
    def _build_where(metadata_filter: dict | None) -> dict | None:
        if not metadata_filter:
            return None
        if len(metadata_filter) == 1:
            ((key, val),) = metadata_filter.items()
            return {key: val}
        return {"$and": [{key: val} for key, val in metadata_filter.items()]}
