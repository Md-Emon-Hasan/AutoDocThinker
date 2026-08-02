from functools import lru_cache

from app.chat.service import ChatService
from app.core.config import get_config
from app.core.environment import env_bool
from app.domain.registry import DomainRegistry
from app.indexing.chroma_store import ChromaStore
from app.indexing.hybrid_index import HybridIndex
from app.ingestion.service import IngestionService
from app.llm.gateway.client import LLMGateway, TaskBoundClient
from app.llm.gateway.models import TaskCategory
from app.llm.gateway.routing import resolve_model
from app.llm.groq_client import GroqClient
from app.llm.wikipedia_client import WikipediaClient
from app.rag.service import RAGService
from app.retrieval.service import RetrievalService


def _build_llm(config):
    """Build the object injected as RAGService's ``llm``.

    When the gateway is enabled (the default), every LLM call goes
    through it with a declared task category, per Stage 1. Setting
    LLM_GATEWAY_ENABLED=false swaps back to the exact pre-Stage-1
    direct-GroqClient object, making the rollout reversible.
    """
    if not env_bool("LLM_GATEWAY_ENABLED", default=True):
        return GroqClient()
    model = resolve_model(TaskCategory.ANSWER_GENERATION, config)
    gateway = LLMGateway(
        providers_by_task={TaskCategory.ANSWER_GENERATION: [GroqClient(model=model)]},
        config=config,
    )
    return TaskBoundClient(gateway, TaskCategory.ANSWER_GENERATION)


@lru_cache
def container() -> dict:
    config = get_config()
    index = HybridIndex()
    dense_index = ChromaStore(domain=config.default_domain)
    domains = DomainRegistry()
    retrieval = RetrievalService(index, dense_index=dense_index)
    rag = RAGService(domains, retrieval, _build_llm(config), WikipediaClient())
    return {
        "config": config,
        "index": index,
        "dense_index": dense_index,
        "domains": domains,
        "retrieval": retrieval,
        "ingestion": IngestionService(index, dense_index=dense_index),
        "rag": rag,
        "chat": ChatService(rag),
    }
