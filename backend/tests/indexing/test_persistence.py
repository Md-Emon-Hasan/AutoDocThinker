"""Consolidated tests for indexing and retrieval modules."""

from threading import RLock

import pytest

from app.indexing.bm25_index import BM25Index
from app.indexing.chroma_store import ChromaStore
from app.indexing.deduplication import already_ingested
from app.indexing.locking import new_lock
from app.indexing.persistence import snapshot_index
from app.indexing.source_registry import SourceRegistry
from app.indexing.stats import index_stats
from app.indexing.tokenizer import tokenize
from app.indexing.vector_index import VectorIndex
from app.ingestion.document import Document
from app.retrieval.bm25_search import bm25_search
from app.retrieval.compressor import compress_documents
from app.retrieval.filters import matches_filter
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.hybrid_search import hybrid_search
from app.retrieval.ranking import top_k
from app.retrieval.reranker import rerank_documents
from app.retrieval.scoring import combine_scores
from app.retrieval.service import RetrievalService, hybrid_retrieve
from app.retrieval.vector_search import vector_search


class TestPersistence:
    def test_snapshot(self, populated_index):
        assert snapshot_index(populated_index)["total_chunks"] == populated_index.size
