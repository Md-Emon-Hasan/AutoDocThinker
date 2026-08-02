import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RAGConfig:
    data_dir: Path = field(default_factory=lambda: ROOT_DIR / "data")
    upload_dir: Path = field(default_factory=lambda: ROOT_DIR / "uploads")
    vector_store_dir: Path = field(
        default_factory=lambda: ROOT_DIR / "data" / "vector_store"
    )
    supported_extensions: tuple[str, ...] = (".pdf", ".docx", ".txt")
    default_domain: str = "general"
    default_mode: str = "advanced"
    initial_k: int = 20
    rerank_top_k: int = 5
    crag_high_confidence: float = 0.6
    crag_low_confidence: float = 0.3
    crag_max_retries: int = 2
    app_name: str = "AutoDocThinker"
    version: str = "3.0.0"
    # Stage 0: dense-store embedding hook, unused by default (see
    # app/indexing/embedding_function.py for why no real ML embedding
    # model is wired in yet).
    embedding_model: str | None = None
    # Stage 1: LLM gateway task -> model routing. Defaults preserve
    # today's single-model behavior (GROQ_MODEL env var, or the
    # historical default) for every task until explicitly configured
    # otherwise.
    task_model_map: dict[str, str] = field(
        default_factory=lambda: {
            "answer_generation": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            "verification": os.getenv(
                "GROQ_VERIFICATION_MODEL",
                os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            ),
            "memory_extraction": os.getenv(
                "GROQ_MEMORY_MODEL",
                os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            ),
            "deep_planning": os.getenv(
                "GROQ_PLANNING_MODEL",
                os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            ),
        }
    )
    escalated_model_map: dict[str, str] = field(default_factory=dict)
    complexity_escalation_threshold: float = 0.7
    # Stage 2: four-layer caching. Disabled entirely via cache_enabled
    # makes every layer a transparent pass-through.
    cache_enabled: bool = True
    embedding_cache_ttl: int = 3600
    embedding_cache_maxsize: int = 2000
    rerank_cache_ttl: int = 1800
    rerank_cache_maxsize: int = 2000
    answer_cache_ttl: int = 600
    answer_cache_maxsize: int = 500
    wikipedia_cache_ttl: int = 3600
    wikipedia_cache_maxsize: int = 200
    # Stage 2: session-scoped index isolation. Ingestion routes default
    # to a fresh private session scope when the caller supplies none --
    # never to "shared", which would silently reproduce the pre-Stage-2
    # leak. auto_ingest (the curated local data_dir corpus) is the one
    # ingestion path that defaults to "shared" instead (see
    # app/ingestion/service.py::auto_ingest).
    default_write_scope: str | None = None
    # Stage 3: Verifier Agent. verification_enabled=False skips the LLM
    # verification call entirely (mechanical citation checks still run,
    # cost-free). Below verification_min_groundedness, at most one
    # regeneration attempt is made (hard-capped, never looped).
    verification_enabled: bool = True
    verification_min_groundedness: float = 0.5
    # Stage 4: Governance layer. Input guard fails closed always (a guard
    # error rejects the request). Output guard fails closed for
    # high-risk domains (see app/governance/policy.py), open-with-warning
    # for General -- a guard crash never becomes a 500 either way.
    governance_enabled: bool = True
    max_input_chars: int = 20_000
    audit_db_path: Path = field(
        default_factory=lambda: ROOT_DIR / "data" / "governance_audit.sqlite3"
    )
    # Stage 4: Human-in-the-loop. Off by default so existing behaviour
    # and tests are unchanged unless explicitly enabled. What gets gated
    # is config-driven: destructive index ops, high-risk-domain answers
    # below the groundedness bar, or any answer below the groundedness
    # bar (verification_min_groundedness, shared with Stage 3).
    hitl_enabled: bool = False
    hitl_gate_destructive_ops: bool = True
    hitl_gate_low_groundedness: bool = True
    hitl_gate_high_risk_domains: bool = True
    hitl_expiry_seconds: float | None = 86_400.0
    hitl_expiry_default_action: str = "reject"
    hitl_db_path: Path = field(
        default_factory=lambda: ROOT_DIR / "data" / "hitl.sqlite3"
    )
    # Stage 5: Long-term & semantic memory. One SQLite store, two record
    # types (episodic turns, semantic facts) -- not two systems.
    # Extraction runs off the request path via BackgroundTasks.
    memory_enabled: bool = True
    memory_extraction_enabled: bool = True
    memory_token_budget: int = 800
    memory_decay_half_life_seconds: float = 30 * 24 * 3600.0  # 30 days
    memory_min_confidence: float = 0.1
    memory_db_path: Path = field(
        default_factory=lambda: ROOT_DIR / "data" / "memory.sqlite3"
    )
    memory_vector_dir: Path = field(
        default_factory=lambda: ROOT_DIR / "data" / "chroma_memory"
    )
    # Stage 6: deep-agent orchestration (planner -> scoped sub-agents ->
    # synthesis), the fifth RAG mode. All caps are hard limits: on
    # exhaustion the orchestrator stops and synthesizes from partial
    # results rather than continuing or truncating silently.
    deep_max_subtasks: int = 5
    deep_max_plan_depth: int = 2
    deep_concurrency: int = 4
    deep_query_timeout_seconds: float = 60.0
    deep_max_llm_calls: int = 12
    deep_max_tokens: int = 20_000
    deep_max_wall_clock_seconds: float = 90.0
    deep_max_recursion_depth: int = 1
    scratchpad_db_path: Path = field(
        default_factory=lambda: ROOT_DIR / "data" / "memory.sqlite3"
    )


def get_config() -> RAGConfig:
    config = RAGConfig()
    config.data_dir.mkdir(parents=True, exist_ok=True)
    config.upload_dir.mkdir(parents=True, exist_ok=True)
    config.vector_store_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("USER_AGENT", "AutoDocThinker/3.0")
    return config
