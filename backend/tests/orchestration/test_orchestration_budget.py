"""All four budget caps; partial synthesis on exhaustion; consumed
budget reported."""

import json

from app.orchestration.budget import Budget, estimate_tokens
from app.orchestration.orchestrator import DeepOrchestrator


class TestBudgetCaps:
    def test_exhausted_on_max_calls(self):
        budget = Budget(
            max_llm_calls=2,
            max_tokens=100_000,
            max_wall_clock_seconds=60,
            max_recursion_depth=1,
        )
        assert not budget.exhausted(depth=1)
        budget.record_call()
        budget.record_call()
        assert budget.exhausted(depth=1)

    def test_exhausted_on_max_tokens(self):
        budget = Budget(
            max_llm_calls=100,
            max_tokens=50,
            max_wall_clock_seconds=60,
            max_recursion_depth=1,
        )
        budget.record_call(tokens=60)
        assert budget.exhausted(depth=1)

    def test_exhausted_on_wall_clock(self):
        budget = Budget(
            max_llm_calls=100,
            max_tokens=100_000,
            max_wall_clock_seconds=0.0,
            max_recursion_depth=1,
        )
        assert budget.exhausted(depth=1)

    def test_depth_within_cap_is_not_exhausted(self):
        budget = Budget(
            max_llm_calls=100,
            max_tokens=100_000,
            max_wall_clock_seconds=60,
            max_recursion_depth=1,
        )
        assert not budget.exhausted(depth=1)

    def test_depth_exceeding_cap_is_exhausted(self):
        budget = Budget(
            max_llm_calls=100,
            max_tokens=100_000,
            max_wall_clock_seconds=60,
            max_recursion_depth=1,
        )
        assert budget.exhausted(depth=2)

    def test_consumed_reports_all_fields(self):
        budget = Budget(
            max_llm_calls=10,
            max_tokens=1000,
            max_wall_clock_seconds=60,
            max_recursion_depth=1,
        )
        budget.record_call(tokens=5)
        consumed = budget.consumed()
        assert consumed["llm_calls"] == 1
        assert consumed["tokens"] == 5
        assert "elapsed_seconds" in consumed


class TestEstimateTokens:
    def test_estimates_roughly_four_chars_per_token(self):
        assert estimate_tokens("x" * 400) == 100

    def test_minimum_one_token(self):
        assert estimate_tokens("") == 1


class _FakeProfile:
    system_prompt = "system prompt"
    name = "general"


class _FakeRetrieval:
    def retrieve(self, query, k, metadata_filter):
        return []


class _PlannerClient:
    def __init__(self, response):
        self.response = response

    def answer(self, *a, **k):
        return self.response


class TestExhaustionSynthesizesPartial:
    def test_llm_call_budget_exhaustion_stops_and_synthesizes_partial(self):
        subtasks = [
            {"id": f"t{i}", "query": f"q{i}", "depends_on": []} for i in range(5)
        ]
        planner = _PlannerClient(json.dumps({"subtasks": subtasks}))

        class _CountingLLM:
            def __init__(self):
                self.calls = 0

            def answer(self, question, context, domain_prompt):
                self.calls += 1
                if "Synthesize" in domain_prompt:
                    return "partial synthesis [1]"
                return f"answer {self.calls}"

        llm = _CountingLLM()
        orchestrator = DeepOrchestrator(
            _FakeRetrieval(),
            llm,
            planner,
            concurrency=1,
            query_timeout_seconds=10.0,
            max_llm_calls=3,  # planner(1) + at most 2 sub-agent calls
            max_tokens=1_000_000,
            max_wall_clock_seconds=60.0,
            max_recursion_depth=1,
            max_subtasks=10,
            max_plan_depth=2,
        )
        long_q = (
            "Please compare and contrast the refund policy and the shipping "
            "policy and explain how they differ from industry standards"
        )
        result = orchestrator.run(long_q, _FakeProfile(), None)
        # Never continues past budget exhaustion -- some sub-tasks skipped.
        assert result["skipped"]
        assert "budget" in result
        assert result["budget"]["llm_calls"] >= 3

    def test_consumed_budget_exposed_in_response(self):
        planner = _PlannerClient(
            json.dumps({"subtasks": [{"id": "t1", "query": "q", "depends_on": []}]})
        )

        class _StubLLM:
            def answer(self, question, context, domain_prompt):
                return "final [1]" if "Synthesize" in domain_prompt else "sub answer"

        orchestrator = DeepOrchestrator(
            _FakeRetrieval(),
            _StubLLM(),
            planner,
            concurrency=2,
            query_timeout_seconds=10.0,
            max_llm_calls=10,
            max_tokens=10_000,
            max_wall_clock_seconds=60.0,
            max_recursion_depth=1,
            max_subtasks=5,
            max_plan_depth=2,
        )
        long_q = (
            "Please compare and contrast the refund policy and the shipping "
            "policy and explain how they differ from industry standards"
        )
        result = orchestrator.run(long_q, _FakeProfile(), None)
        assert result["budget"]["llm_calls"] > 0
        assert result["budget"]["max_llm_calls"] == 10
