import math
from collections import Counter

from app.utils.cache import MISSING
from app.utils.hashing import sha1_short

_CACHE_VERSION = "tfidf-v1"


def _tfidf_score(query_terms: list[str], doc_text: str, all_docs: list) -> float:
    doc_tokens = doc_text.lower().split()
    tf_map = Counter(doc_tokens)
    doc_len = max(len(doc_tokens), 1)
    n = max(len(all_docs), 1)
    score = 0.0
    for term in query_terms:
        tf = tf_map.get(term, 0)
        if tf == 0:
            continue
        df = sum(1 for d in all_docs if term in d.page_content.lower().split())
        idf = math.log((n + 1) / (df + 1)) + 1
        score += (tf / doc_len) * idf
    return score


def rerank_documents(query: str, docs: list, limit: int, cache=None) -> list:
    """Rerank docs by TF-IDF score against ``query``. ``cache`` keys on
    (query, chunk id) to skip recomputing the heaviest CPU work in the
    request path on every retrieval."""
    if not docs:
        return docs
    query_terms = query.lower().split()
    query_key = sha1_short(query) if cache is not None else None
    scored = []
    for doc in docs:
        cache_key = None
        if cache is not None:
            chunk_id = doc.metadata.get("chunk_id", doc.page_content[:50])
            cache_key = f"{query_key}::{chunk_id}::{_CACHE_VERSION}"
            cached_score = cache.get(cache_key)
            if cached_score is not MISSING:
                scored.append((cached_score, doc))
                continue
        score = _tfidf_score(query_terms, doc.page_content, docs)
        if cache is not None:
            cache.set(cache_key, score)
        scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in scored[:limit]]
