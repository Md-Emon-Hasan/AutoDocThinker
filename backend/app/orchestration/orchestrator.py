import logging
from concurrent.futures import (
    ThreadPoolExecutor,
)
from concurrent.futures import TimeoutError as FutureTimeoutError
from concurrent.futures import (
    as_completed,
)
from uuid import uuid4

from app.orchestration.budget import Budget, estimate_tokens
from app.orchestration.planner import Planner
from app.orchestration.subagent import SubAgent
from app.orchestration.synthesis import synthesize

logger = logging.getLogger(__name__)


class DeepOrchestrator:
    """Planner -> scoped sub-agents (parallel, dependency-graph aware,
    concurrency-capped) -> synthesis. The `deep` mode's real
    implementation.

    Uses ThreadPoolExecutor instead of asyncio.gather since this codebase
    is fully synchronous. Sub-agents never spawn further sub-agents (one
    decomposition level only), so max_recursion_depth is enforced
    defensively but never actually reached.
    """

    def __init__(
        self,
        retrieval,
        llm,
        planner_task_client,
        concurrency: int,
        query_timeout_seconds: float,
        max_llm_calls: int,
        max_tokens: int,
        max_wall_clock_seconds: float,
        max_recursion_depth: int,
        max_subtasks: int,
        max_plan_depth: int,
        scratchpad_store=None,
    ) -> None:
        self.retrieval = retrieval
        self.llm = llm
        self.planner = Planner(
            planner_task_client, max_subtasks=max_subtasks, max_depth=max_plan_depth
        )
        self.concurrency = concurrency
        self.query_timeout_seconds = query_timeout_seconds
        self._budget_kwargs = {
            "max_llm_calls": max_llm_calls,
            "max_tokens": max_tokens,
            "max_wall_clock_seconds": max_wall_clock_seconds,
            "max_recursion_depth": max_recursion_depth,
        }
        self.scratchpad_store = scratchpad_store

    def _dispatch_round(
        self, ready, subagent, results, budget, query_id
    ) -> tuple[set, bool]:
        """Dispatch one round of independent, ready sub-tasks
        concurrently. Returns (completed_ids, budget_hit_mid_round)."""
        completed_ids: set[str] = set()
        budget_hit = False
        with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
            futures = {executor.submit(subagent.run, t): t.id for t in ready}
            try:
                for future in as_completed(futures, timeout=self.query_timeout_seconds):
                    subtask_id = futures[future]
                    result = future.result()
                    results[subtask_id] = result
                    completed_ids.add(subtask_id)
                    budget.record_call(tokens=estimate_tokens(result.answer))
                    if self.scratchpad_store is not None:
                        self.scratchpad_store.update_status(
                            query_id,
                            subtask_id,
                            "done" if result.success else "failed",
                            note=result.error,
                        )
                    if budget.exhausted(depth=1):
                        # Stop waiting on the rest of this round -- never
                        # continue past exhaustion. Futures not yet
                        # started are cancelled; already-running ones
                        # finish but their results are dropped.
                        budget_hit = True
                        for other in futures:
                            other.cancel()
                        break
            except FutureTimeoutError:
                # Per-query wall-clock timeout: synthesize from whatever
                # completed. Tasks that didn't finish in time are simply
                # not in completed_ids -> reported as skipped by the
                # caller, not silently dropped.
                logger.warning(
                    "Deep orchestration: query timeout, synthesizing partial results"
                )
        return completed_ids, budget_hit

    def run(self, question: str, domain_profile, metadata_filter) -> dict:
        budget = Budget(**self._budget_kwargs)
        query_id = str(uuid4())

        subtasks, planner_called = self.planner.plan(question)
        if planner_called:
            budget.record_call(tokens=estimate_tokens(question))
        if self.scratchpad_store is not None:
            self.scratchpad_store.save(query_id, question, subtasks)

        subagent = SubAgent(self.retrieval, self.llm, domain_profile, metadata_filter)
        results: dict[str, object] = {}
        remaining = {t.id: t for t in subtasks}

        while remaining and not budget.exhausted(depth=1):
            ready = [
                t for t in remaining.values() if all(d in results for d in t.depends_on)
            ]
            if not ready:
                # Circular or unsatisfiable dependency -- stop here and
                # synthesize from whatever completed rather than hang.
                logger.warning(
                    "Deep orchestration: unsatisfiable dependency graph, "
                    "%d sub-task(s) skipped",
                    len(remaining),
                )
                break

            completed_ids, budget_hit_mid_round = self._dispatch_round(
                ready, subagent, results, budget, query_id
            )
            for subtask_id in completed_ids:
                remaining.pop(subtask_id, None)
            if budget_hit_mid_round:
                break

        skipped = list(remaining.keys())
        synthesis = synthesize(
            question, list(results.values()), self.llm, domain_profile, skipped
        )
        budget.record_call(tokens=estimate_tokens(synthesis["answer"]))
        synthesis["budget"] = budget.consumed()
        synthesis["query_id"] = query_id
        return synthesis
