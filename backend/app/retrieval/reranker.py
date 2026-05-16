import math
from collections import Counter


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


def rerank_documents(query: str, docs: list, limit: int) -> list:
    if not docs:
        return docs
    query_terms = query.lower().split()
    scored = [(_tfidf_score(query_terms, doc.page_content, docs), doc) for doc in docs]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in scored[:limit]]
