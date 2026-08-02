from app.memory.retrieval import format_memory_section, select_facts_within_budget
from app.orchestration.planner import is_trivial
from app.rag.formatting import format_context_with_sources
from app.rag.modes import ensure_mode
from app.retrieval.filters import scope_filter
from app.utils.cache import MISSING
from app.utils.hashing import sha1_short
from app.workflows.advanced import run_advanced
from app.workflows.crag import run_crag
from app.workflows.deep import run_deep
from app.workflows.finalize import finalize
from app.workflows.naive import run_naive
from app.workflows.self_rag import run_self_rag

# Answer-generation temperature is fixed at 0.0 (see app/llm/groq_client.py)
# so this constant documents that the cache key's "temperature" component is
# always this value today -- if a future non-deterministic path is added,
# its calls must bypass the answer cache rather than share this key shape.
_ANSWER_TEMPERATURE = 0.0


def _plan_signature(mode: str, question: str) -> str:
    """`deep` needs a plan component in its cache key since a different
    decomposition is a different computation. Uses the free, deterministic
    is_trivial() check as a proxy instead of running the planner (which
    would defeat caching away the planner call itself)."""
    if mode != "deep":
        return ""
    return "trivial" if is_trivial(question) else "decomposed"


def _answer_cache_key(
    question: str,
    mode: str,
    domain: str,
    index_version: int,
    model: str,
    scope,
    memory_version: int = 0,
) -> str:
    normalized_question = " ".join(question.strip().lower().split())
    parts = "::".join(
        [
            normalized_question,
            mode,
            domain,
            str(index_version),
            model,
            str(_ANSWER_TEMPERATURE),
            scope or "",
            str(memory_version),
            _plan_signature(mode, question),
        ]
    )
    return sha1_short(parts, length=32)


class RAGService:
    def __init__(
        self,
        domains,
        retrieval,
        llm,
        wiki,
        cache_manager=None,
        verifier=None,
        verification_min_groundedness: float = 0.5,
        input_guard=None,
        output_guard=None,
        audit_log=None,
        hitl_gate=None,
        memory_store=None,
        fact_index=None,
        memory_token_budget: int = 800,
        orchestrator=None,
    ) -> None:
        self.domains = domains
        self.retrieval = retrieval
        self.llm = llm
        self.wiki = wiki
        self.cache_manager = cache_manager
        self.verifier = verifier
        self.verification_min_groundedness = verification_min_groundedness
        self.input_guard = input_guard
        self.output_guard = output_guard
        self.audit_log = audit_log
        self.hitl_gate = hitl_gate
        self.memory_store = memory_store
        self.fact_index = fact_index
        self.memory_token_budget = memory_token_budget
        self.orchestrator = orchestrator

    def _answer_cache(self):
        if self.cache_manager is not None and self.cache_manager.enabled:
            return self.cache_manager.answer
        return None

    def _cached_response(
        self, cached: dict, clean_mode: str, profile, question, history
    ) -> dict:
        turn_state = finalize(
            {"input": question, "history": history or [], "answer": cached["answer"]}
        )
        response = {
            "answer": cached["answer"],
            "sources": cached["sources"],
            "history": turn_state["history"],
            "mode": clean_mode,
            "domain": profile.name,
            "metadata": cached["metadata"],
        }
        # A verified cached answer is not re-verified.
        if "verification" in cached:
            response["verification"] = cached["verification"]
        return response

    def _dispatch(self, clean_mode: str, state: dict, profile):
        if clean_mode == "naive":
            return run_naive(state, self.retrieval, self.llm, profile)
        if clean_mode == "advanced":
            return run_advanced(state, self.retrieval, self.llm, profile)
        if clean_mode == "crag":
            return run_crag(state, self.retrieval, self.llm, profile, self.wiki)
        if clean_mode == "deep":
            return run_deep(state, self.retrieval, self.llm, profile, self.orchestrator)
        return run_self_rag(state, self.retrieval, self.llm, profile)

    def _apply_verification(
        self, question: str, response: dict, result: dict, profile
    ) -> None:
        """Attach verification fields to ``response``, regenerating at
        most once if groundedness falls below threshold."""
        context_text, _ = format_context_with_sources(result.get("context_docs", []))
        verification = self.verifier.verify(
            question, response["answer"], context_text, response["sources"]
        )
        if (
            verification.verified
            and verification.groundedness is not None
            and verification.groundedness < self.verification_min_groundedness
        ):
            # At most one regeneration attempt, hard-capped -- an
            # uncapped verify-then-regenerate cycle is an unbounded cost
            # leak. The regenerated answer is not re-verified.
            feedback = (
                f"{context_text}\n\nNote: a previous draft made these claims "
                "without adequate support in the retrieved context -- avoid "
                f"asserting them without evidence: {verification.unsupported_claims}"
            )
            response["answer"] = self.llm.answer(
                question, feedback, profile.system_prompt
            )
            verification = verification.__class__(
                groundedness=verification.groundedness,
                claims=verification.claims,
                unsupported_claims=verification.unsupported_claims,
                citation_issues=verification.citation_issues,
                verified=True,
                regenerated=True,
            )
        response["verification"] = verification.to_dict()

    def _blocked_response(
        self, clean_mode: str, profile, history, rules_fired: list[str]
    ) -> dict:
        return {
            "answer": "This request was blocked by governance and could not be processed.",
            "sources": [],
            "history": history or [],
            "mode": clean_mode,
            "domain": profile.name,
            "metadata": {},
            "governance": {"blocked": True, "rules_fired": rules_fired},
        }

    def _apply_output_guard(self, response: dict, domain: str) -> None:
        result = self.output_guard.check(
            response["answer"], domain, response.get("verification")
        )
        governance = {"blocked": not result.allowed, "rules_fired": result.rules_fired}
        if result.warning:
            governance["warning"] = result.warning
        if not result.allowed:
            response["answer"] = (
                "This response was blocked by governance policy for this domain."
            )
            response["sources"] = []
        elif result.redacted_text:
            governance["pii_redacted"] = True
        response["governance"] = governance
        if self.audit_log is not None and result.rules_fired:
            self.audit_log.record(
                None,
                ",".join(result.rules_fired),
                "blocked" if not result.allowed else "allowed_with_warning",
            )

    def _apply_hitl(self, response: dict, domain: str, scope) -> dict | None:
        gated, kind = self.hitl_gate.should_gate_answer(
            domain, response.get("verification")
        )
        if not gated:
            return None
        pending = self.hitl_gate.create_pending(kind, f"gated: {kind}", response, scope)
        if self.audit_log is not None:
            self.audit_log.record(scope, kind, "gated_pending")
        return {
            "answer": "This answer requires human approval before it can be returned.",
            "sources": [],
            "history": response["history"],
            "mode": response["mode"],
            "domain": response["domain"],
            "metadata": {},
            "hitl": {"pending": True, "pending_id": pending["id"], "kind": kind},
        }

    def _check_input_guard(
        self, question: str, clean_mode: str, profile, history, scope
    ) -> tuple[str, dict | None]:
        """Returns (possibly-redacted question, blocked_response_or_None)."""
        if self.input_guard is None:
            return question, None
        guard_result = self.input_guard.check(question)
        if not guard_result.allowed:
            if self.audit_log is not None:
                self.audit_log.record(
                    scope, ",".join(guard_result.rules_fired), "blocked"
                )
            blocked = self._blocked_response(
                clean_mode, profile, history, guard_result.rules_fired
            )
            return question, blocked
        if guard_result.redacted_text is not None:
            question = guard_result.redacted_text
        return question, None

    def _memory_version(self) -> int:
        return self.memory_store.version if self.memory_store is not None else 0

    def _check_cache(self, question, clean_mode, profile, scope, history):
        """Returns (cache_or_None, cache_key_or_None, cached_response_or_None)."""
        cache = self._answer_cache()
        if cache is None:
            return None, None, None
        model = getattr(self.llm, "model_name", "unknown")
        cache_key = _answer_cache_key(
            question,
            clean_mode,
            profile.name,
            self.retrieval.index.version,
            model,
            scope,
            self._memory_version(),
        )
        cached = cache.get(cache_key)
        if cached is MISSING:
            return cache, cache_key, None
        return (
            cache,
            cache_key,
            self._cached_response(cached, clean_mode, profile, question, history),
        )

    def _memory_augmented_formatter(self, scope: str | None, question: str):
        """Wrap format_context_with_sources so retrieved facts enter the
        prompt as a clearly delimited section, distinct from retrieved
        document context -- without touching any workflow node's logic
        (nodes.py always calls whatever callable RAGService injects as
        ``state["formatter"]``)."""
        if self.memory_store is None or not scope:
            return format_context_with_sources

        facts = self.memory_store.list_facts(scope)
        if self.fact_index is not None and facts:
            relevant_ids = set(self.fact_index.search(scope, question, k=len(facts)))
            facts = [f for f in facts if f.id in relevant_ids] or facts
        selected = select_facts_within_budget(facts, self.memory_token_budget)
        memory_section = format_memory_section(selected)

        def _formatter(docs):
            context, sources = format_context_with_sources(docs)
            return context + memory_section, sources

        return _formatter

    def query(
        self,
        question: str,
        domain: str,
        mode: str,
        history=None,
        metadata_filter=None,
        scope: str | None = None,
    ) -> dict:
        clean_mode = ensure_mode(mode)
        profile = self.domains.get(domain)

        question, blocked = self._check_input_guard(
            question, clean_mode, profile, history, scope
        )
        if blocked is not None:
            return blocked

        merged_filter = {
            **profile.metadata_filter,
            **(metadata_filter or {}),
            **scope_filter(scope),
        }

        cache, cache_key, cached_response = self._check_cache(
            question, clean_mode, profile, scope, history
        )
        if cached_response is not None:
            return cached_response

        state = {
            "input": question,
            "domain": profile.name,
            "mode": clean_mode,
            "history": history or [],
            "metadata_filter": merged_filter or None,
            "formatter": self._memory_augmented_formatter(scope, question),
        }
        result = finalize(self._dispatch(clean_mode, state, profile))
        response = {
            "answer": result["answer"],
            "sources": result.get("sources", []),
            "history": result["history"],
            "mode": clean_mode,
            "domain": profile.name,
            "metadata": {
                key: result[key]
                for key in (
                    "confidence",
                    "need_retrieval",
                    "rewritten_queries",
                    "orchestration",
                )
                if key in result
            },
        }

        if self.verifier is not None and response["answer"]:
            self._apply_verification(question, response, result, profile)

        if self.output_guard is not None and response["answer"]:
            self._apply_output_guard(response, profile.name)

        if self.hitl_gate is not None and response["answer"]:
            pending_response = self._apply_hitl(response, profile.name, scope)
            if pending_response is not None:
                # A gated request must not hold an open HTTP connection
                # waiting for a human -- return a pending id immediately,
                # and never cache a pending (not-yet-approved) answer.
                return pending_response

        # Never cache a failure/empty answer.
        if cache is not None and response["answer"]:
            to_cache = {
                "answer": response["answer"],
                "sources": response["sources"],
                "metadata": response["metadata"],
            }
            if "verification" in response:
                to_cache["verification"] = response["verification"]
            cache.set(cache_key, to_cache)
        return response


def process_query(
    rag_service: RAGService,
    input_text: str,
    file_path=None,
    file_type=None,
    mode: str = "advanced",
    history=None,
    metadata_filter=None,
    domain: str = "general",
    scope: str | None = None,
) -> dict:
    if file_path or file_type:
        metadata_filter = metadata_filter or {}
    return rag_service.query(
        input_text, domain, mode, history or [], metadata_filter, scope
    )
