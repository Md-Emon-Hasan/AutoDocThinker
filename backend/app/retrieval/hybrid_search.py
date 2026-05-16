from app.retrieval.bm25_search import bm25_search
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.vector_search import vector_search


def hybrid_search(index, query: str, k: int, metadata_filter=None) -> list:
    return reciprocal_rank_fusion(
        [
            vector_search(index, query, k, metadata_filter),
            bm25_search(index, query, k, metadata_filter),
        ],
        k,
    )
