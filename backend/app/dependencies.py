from functools import lru_cache

from app.chat.history_store import HistoryStore
from app.chat.service import ChatService
from app.core.config import get_config
from app.core.environment import env_bool
from app.domain.registry import DomainRegistry
from app.governance.audit import AuditLog
from app.governance.input_guard import InputGuard
from app.governance.output_guard import OutputGuard
from app.hitl.gate import HITLGate
from app.hitl.store import HITLStore
from app.indexing.chroma_store import ChromaStore
from app.indexing.hybrid_index import HybridIndex
from app.ingestion.service import IngestionService
from app.llm.gateway.client import LLMGateway, TaskBoundClient
from app.llm.gateway.models import TaskCategory
from app.llm.gateway.routing import resolve_model
from app.llm.groq_client import GroqClient
from app.llm.wikipedia_client import WikipediaClient
from app.memory.semantic import FactIndex
from app.memory.store import MemoryStore
from app.orchestration.orchestrator import DeepOrchestrator
from app.orchestration.scratchpad import ScratchpadStore
from app.rag.service import RAGService
from app.retrieval.service import RetrievalService
from app.utils.cache import CacheManager
from app.verification.agent import VerifierAgent


def _build_llm(config):
    """Build (answer_llm, gateway) for RAGService and the task-bound
    clients. LLM_GATEWAY_ENABLED=false bypasses the gateway entirely,
    falling back to a bare GroqClient with no other LLM-backed features.
    """
    if not env_bool("LLM_GATEWAY_ENABLED", default=True):
        return GroqClient(), None
    answer_model = resolve_model(TaskCategory.ANSWER_GENERATION, config)
    verification_model = resolve_model(TaskCategory.VERIFICATION, config)
    memory_model = resolve_model(TaskCategory.MEMORY_EXTRACTION, config)
    planning_model = resolve_model(TaskCategory.DEEP_PLANNING, config)
    gateway = LLMGateway(
        providers_by_task={
            TaskCategory.ANSWER_GENERATION: [GroqClient(model=answer_model)],
            TaskCategory.VERIFICATION: [GroqClient(model=verification_model)],
            TaskCategory.MEMORY_EXTRACTION: [GroqClient(model=memory_model)],
            TaskCategory.DEEP_PLANNING: [GroqClient(model=planning_model)],
        },
        config=config,
    )
    return TaskBoundClient(gateway, TaskCategory.ANSWER_GENERATION), gateway


def _build_verifier(config, gateway):
    if not config.verification_enabled or gateway is None:
        return VerifierAgent(task_client=None)
    return VerifierAgent(
        task_client=TaskBoundClient(gateway, TaskCategory.VERIFICATION)
    )


def _build_memory_extraction_client(config, gateway):
    if not config.memory_extraction_enabled or gateway is None:
        return None
    return TaskBoundClient(gateway, TaskCategory.MEMORY_EXTRACTION)


def _build_orchestrator(config, gateway, retrieval, answer_llm, scratchpad_store):
    planner_client = (
        TaskBoundClient(gateway, TaskCategory.DEEP_PLANNING)
        if gateway is not None
        else None
    )
    return DeepOrchestrator(
        retrieval,
        answer_llm,
        planner_client,
        concurrency=config.deep_concurrency,
        query_timeout_seconds=config.deep_query_timeout_seconds,
        max_llm_calls=config.deep_max_llm_calls,
        max_tokens=config.deep_max_tokens,
        max_wall_clock_seconds=config.deep_max_wall_clock_seconds,
        max_recursion_depth=config.deep_max_recursion_depth,
        max_subtasks=config.deep_max_subtasks,
        max_plan_depth=config.deep_max_plan_depth,
        scratchpad_store=scratchpad_store,
    )


@lru_cache
def container() -> dict:
    config = get_config()
    cache_manager = CacheManager.from_config(config)
    index = HybridIndex()
    dense_index = ChromaStore(domain=config.default_domain, cache_manager=cache_manager)
    domains = DomainRegistry()
    retrieval = RetrievalService(
        index, dense_index=dense_index, cache_manager=cache_manager
    )
    answer_llm, gateway = _build_llm(config)

    audit_log = AuditLog(config.audit_db_path)
    hitl_store = HITLStore(config.hitl_db_path)
    hitl_gate = HITLGate(hitl_store, config)
    input_guard = InputGuard(max_input_chars=config.max_input_chars)
    output_guard = OutputGuard()
    governance_enabled = config.governance_enabled

    memory_store = MemoryStore(config.memory_db_path) if config.memory_enabled else None
    fact_index = (
        FactIndex(config.memory_vector_dir, cache_manager=cache_manager)
        if config.memory_enabled
        else None
    )
    memory_extraction_client = (
        _build_memory_extraction_client(config, gateway)
        if config.memory_enabled
        else None
    )
    history_store = HistoryStore(memory_store=memory_store)
    scratchpad_store = ScratchpadStore(config.scratchpad_db_path)
    orchestrator = _build_orchestrator(
        config, gateway, retrieval, answer_llm, scratchpad_store
    )

    rag = RAGService(
        domains,
        retrieval,
        answer_llm,
        WikipediaClient(
            cache=cache_manager.wikipedia if cache_manager.enabled else None
        ),
        cache_manager=cache_manager,
        verifier=_build_verifier(config, gateway),
        verification_min_groundedness=config.verification_min_groundedness,
        input_guard=input_guard if governance_enabled else None,
        output_guard=output_guard if governance_enabled else None,
        audit_log=audit_log,
        hitl_gate=hitl_gate if hitl_gate.enabled else None,
        memory_store=memory_store,
        fact_index=fact_index,
        memory_token_budget=config.memory_token_budget,
        orchestrator=orchestrator,
    )
    return {
        "config": config,
        "cache_manager": cache_manager,
        "index": index,
        "dense_index": dense_index,
        "domains": domains,
        "retrieval": retrieval,
        "ingestion": IngestionService(index, dense_index=dense_index),
        "rag": rag,
        "chat": ChatService(rag, history_store=history_store),
        "audit_log": audit_log,
        "hitl_store": hitl_store,
        "hitl_gate": hitl_gate,
        "memory_store": memory_store,
        "fact_index": fact_index,
        "memory_extraction_client": memory_extraction_client,
        "scratchpad_store": scratchpad_store,
        "orchestrator": orchestrator,
    }
