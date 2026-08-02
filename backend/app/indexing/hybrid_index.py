from typing import Any
from uuid import uuid4

from rank_bm25 import BM25Okapi

from app.indexing.deduplication import already_ingested
from app.indexing.locking import new_lock
from app.indexing.tokenizer import tokenize

DEFAULT_SCOPE = "shared"


class HybridIndex:
    def __init__(self) -> None:
        self._lock = new_lock()
        self._chunks: list[Any] = []
        self._source_ids: set[str] = set()
        self._source_map: dict[str, str] = {}  # source_id → display name

    def _candidates(self, metadata_filter: dict | None) -> list[Any]:
        """Restrict the corpus to matching documents BEFORE BM25 scoring.

        Filtering after scoring would compute IDF/avg-doc-len over the wrong
        corpus (the whole index instead of the scoped subset), silently
        skewing relevance for any caller that passes a metadata filter.
        """
        if not metadata_filter:
            return list(self._chunks)
        return [
            doc
            for doc in self._chunks
            if not any(
                doc.metadata.get(key) != val for key, val in metadata_filter.items()
            )
        ]

    def clear(self) -> None:
        with self._lock:
            self._chunks = []
            self._source_ids = set()
            self._source_map = {}

    def add(self, chunks: list) -> int:
        if not chunks:
            return 0
        incoming = {chunk.metadata.get("source_id", "") for chunk in chunks}
        with self._lock:
            if already_ingested(self._source_ids, incoming):
                return 0
            for chunk in chunks:
                chunk.metadata["chunk_id"] = chunk.metadata.get("chunk_id") or str(
                    uuid4()
                )
                chunk.metadata.setdefault("scope", DEFAULT_SCOPE)
                sid = chunk.metadata["source_id"]
                self._chunks.append(chunk)
                self._source_ids.add(sid)
                self._source_map[sid] = chunk.metadata.get("source", sid)
            return len(chunks)

    def remove_source(self, source_id: str) -> bool:
        with self._lock:
            if source_id not in self._source_ids:
                return False
            self._chunks = [
                c for c in self._chunks if c.metadata.get("source_id") != source_id
            ]
            self._source_ids.discard(source_id)
            self._source_map.pop(source_id, None)
            return True

    def search(
        self, query: str, k: int = 8, metadata_filter: dict | None = None
    ) -> list:
        q_tokens = tokenize(query)
        if not q_tokens:
            return []
        with self._lock:
            candidates = self._candidates(metadata_filter)
            if not candidates:
                return []
            tokenized_docs = [tokenize(doc.page_content) for doc in candidates]
            bm25 = BM25Okapi(tokenized_docs)
            scores = bm25.get_scores(q_tokens)
        query_terms = set(q_tokens)
        # BM25 scores can legitimately go negative on tiny corpora (a term
        # appearing in most/all documents gets a negative idf) — that's not
        # a signal of "no match", so rank by score but only keep documents
        # that actually contain at least one query term.
        ranked = sorted(
            zip(scores, candidates, tokenized_docs),
            key=lambda item: item[0],
            reverse=True,
        )
        return [
            doc for _, doc, doc_tokens in ranked[:k] if query_terms & set(doc_tokens)
        ]

    @property
    def size(self) -> int:
        return len(self._chunks)

    @property
    def sources(self) -> list[str]:
        return sorted(self._source_map.values())

    @property
    def source_details(self) -> list[dict]:
        return sorted(
            [
                {"source_id": sid, "name": name}
                for sid, name in self._source_map.items()
            ],
            key=lambda x: x["name"],
        )
