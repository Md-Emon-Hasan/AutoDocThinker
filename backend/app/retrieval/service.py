from app.retrieval.bm25_search import bm25_search
from app.retrieval.compressor import compress_documents
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.reranker import rerank_documents
from app.retrieval.vector_search import vector_search


class RetrievalService:
    def __init__(self, index, dense_index=None, cache_manager=None) -> None:
        self.index = index
        self.dense_index = dense_index
        self.cache_manager = cache_manager

    def retrieve(self, query: str, k: int, metadata_filter: dict | None = None) -> list:
        # Retrieve more candidates for better reranking coverage
        candidates = k * 3
        if self.dense_index is not None:
            # Genuine dense+sparse fusion: two independent result sets,
            # combined via reciprocal rank fusion.
            groups = [
                vector_search(self.dense_index, query, candidates, metadata_filter),
                bm25_search(self.index, query, candidates, metadata_filter),
            ]
        else:
            groups = [
                self.index.search(query, k=candidates, metadata_filter=metadata_filter)
            ]
        fused = reciprocal_rank_fusion(groups, candidates)
        rerank_cache = (
            self.cache_manager.rerank
            if self.cache_manager is not None and self.cache_manager.enabled
            else None
        )
        reranked = rerank_documents(query, fused, k, cache=rerank_cache)
        return compress_documents(reranked)


def hybrid_retrieve(
    index, query: str, k: int, metadata_filter: dict | None = None
) -> list:
    return RetrievalService(index).retrieve(query, k, metadata_filter)
