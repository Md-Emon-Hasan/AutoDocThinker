from app.retrieval.compressor import compress_documents
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.reranker import rerank_documents


class RetrievalService:
    def __init__(self, index) -> None:
        self.index = index

    def retrieve(self, query: str, k: int, metadata_filter: dict | None = None) -> list:
        # Retrieve more candidates for better reranking coverage
        candidates = k * 3
        lexical = self.index.search(
            query, k=candidates, metadata_filter=metadata_filter
        )
        fused = reciprocal_rank_fusion([lexical], candidates)
        reranked = rerank_documents(query, fused, k)
        return compress_documents(reranked)


def hybrid_retrieve(
    index, query: str, k: int, metadata_filter: dict | None = None
) -> list:
    return RetrievalService(index).retrieve(query, k, metadata_filter)
