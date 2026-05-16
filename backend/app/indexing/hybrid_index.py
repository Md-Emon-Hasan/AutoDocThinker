import math
from collections import Counter
from threading import RLock
from typing import Any
from uuid import uuid4

from app.indexing.deduplication import already_ingested
from app.indexing.tokenizer import tokenize


class HybridIndex:
    def __init__(self) -> None:
        self._lock = RLock()
        self._chunks: list[Any] = []
        self._source_ids: set[str] = set()
        self._source_map: dict[str, str] = {}  # source_id → display name
        # BM25 parameters
        self._k1 = 1.5
        self._b = 0.75
        self._doc_freqs: dict[str, int] = {}  # term → number of docs containing term
        self._avg_doc_len: float = 0.0

    def _rebuild_stats(self) -> None:
        if not self._chunks:
            self._doc_freqs = {}
            self._avg_doc_len = 0.0
            return
        total_len = 0
        df: dict[str, int] = {}
        for doc in self._chunks:
            tokens = tokenize(doc.page_content)
            total_len += len(tokens)
            for term in set(tokens):
                df[term] = df.get(term, 0) + 1
        self._doc_freqs = df
        self._avg_doc_len = total_len / len(self._chunks)

    def _bm25_score(self, query_tokens: list[str], doc_tokens: list[str]) -> float:
        if not query_tokens or not doc_tokens or not self._avg_doc_len:
            return 0.0
        n = len(self._chunks)
        doc_len = len(doc_tokens)
        tf_map = Counter(doc_tokens)
        score = 0.0
        for term in query_tokens:
            if term not in tf_map:
                continue
            df = self._doc_freqs.get(term, 0)
            idf = math.log((n - df + 0.5) / (df + 0.5) + 1)
            tf = tf_map[term]
            norm_tf = (
                tf
                * (self._k1 + 1)
                / (
                    tf
                    + self._k1 * (1 - self._b + self._b * doc_len / self._avg_doc_len)
                )
            )
            score += idf * norm_tf
        return score

    def clear(self) -> None:
        with self._lock:
            self._chunks = []
            self._source_ids = set()
            self._source_map = {}
            self._doc_freqs = {}
            self._avg_doc_len = 0.0

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
                sid = chunk.metadata["source_id"]
                self._chunks.append(chunk)
                self._source_ids.add(sid)
                self._source_map[sid] = chunk.metadata.get("source", sid)
            self._rebuild_stats()
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
            self._rebuild_stats()
            return True

    def search(
        self, query: str, k: int = 8, metadata_filter: dict | None = None
    ) -> list:
        q_tokens = tokenize(query)
        scored = []
        with self._lock:
            for doc in self._chunks:
                if metadata_filter and any(
                    doc.metadata.get(key) != val for key, val in metadata_filter.items()
                ):
                    continue
                d_tokens = tokenize(doc.page_content)
                score = self._bm25_score(q_tokens, d_tokens)
                if score > 0:
                    scored.append((score, doc))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [doc for _, doc in scored[:k]]

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
