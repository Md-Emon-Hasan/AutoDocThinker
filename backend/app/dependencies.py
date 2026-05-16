from functools import lru_cache

from app.chat.service import ChatService
from app.core.config import get_config
from app.domain.registry import DomainRegistry
from app.indexing.hybrid_index import HybridIndex
from app.ingestion.service import IngestionService
from app.llm.groq_client import GroqClient
from app.llm.wikipedia_client import WikipediaClient
from app.rag.service import RAGService
from app.retrieval.service import RetrievalService


@lru_cache
def container() -> dict:
    index = HybridIndex()
    domains = DomainRegistry()
    retrieval = RetrievalService(index)
    rag = RAGService(domains, retrieval, GroqClient(), WikipediaClient())
    return {
        "config": get_config(),
        "index": index,
        "domains": domains,
        "retrieval": retrieval,
        "ingestion": IngestionService(index),
        "rag": rag,
        "chat": ChatService(rag),
    }
