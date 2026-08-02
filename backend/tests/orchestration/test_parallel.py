"""Independent sub-tasks run concurrently, dependencies are respected,
the concurrency cap is enforced, and one failure doesn't cancel the batch."""

import json
import threading
import time

from app.orchestration.orchestrator import DeepOrchestrator


class _FakeProfile:
    system_prompt = "system prompt"
    name = "general"


class _FakeRetrieval:
    def retrieve(self, query, k, metadata_filter):
        return []


class _PlannerClient:
    """Returns a fixed decomposition; not used for sub-agent/synthesis
    calls in these tests (a separate llm stub handles those)."""

    def __init__(self, subtasks_json):
        self._response = subtasks_json

    def answer(self, question, context, domain_prompt):
        return self._response


def _plan_response(subtasks):
    return json.dumps({"subtasks": subtasks})


class _ConcurrencyTrackingLLM:
    """Records the max number of concurrently in-flight .answer() calls,
    and how long each sub-task call took, to prove real parallel
    dispatch (not serial) and that the concurrency cap is respected."""

    def __init__(self, delay=0.05):
        self.delay = delay
        self.lock = threading.Lock()
        self.in_flight = 0
        self.max_in_flight = 0
        self.calls = []

    def answer(self, question, context, domain_prompt):
        if "Synthesize" in domain_prompt:
            return "final synthesized answer [1]"
        with self.lock:
            self.in_flight += 1
            self.max_in_flight = max(self.max_in_flight, self.in_flight)
        time.sleep(self.delay)
        with self.lock:
            self.in_flight -= 1
            self.calls.append(question)
        return f"answer for {question}"


def _make_orchestrator(llm, subtasks, concurrency=4, timeout=10.0):
    return DeepOrchestrator(
        _FakeRetrieval(),
        llm,
        _PlannerClient(_plan_response(subtasks)),
        concurrency=concurrency,
        query_timeout_seconds=timeout,
        max_llm_calls=100,
        max_tokens=100_000,
        max_wall_clock_seconds=60.0,
        max_recursion_depth=1,
        max_subtasks=10,
        max_plan_depth=2,
    )


class TestParallelDispatch:
    def test_independent_subtasks_run_concurrently(self):
        subtasks = [
            {"id": f"t{i}", "query": f"q{i}", "depends_on": []} for i in range(4)
        ]
        llm = _ConcurrencyTrackingLLM(delay=0.05)
        orchestrator = _make_orchestrator(llm, subtasks, concurrency=4)
        result = orchestrator.run(
            "Please compare and contrast the refund policy and the shipping policy and explain how they differ from industry standards in full detail",
            _FakeProfile(),
            None,
        )
        assert llm.max_in_flight > 1  # genuinely overlapped, not serial
        assert set(result["succeeded"]) == {"t0", "t1", "t2", "t3"}

    def test_concurrency_cap_is_respected(self):
        subtasks = [
            {"id": f"t{i}", "query": f"q{i}", "depends_on": []} for i in range(6)
        ]
        llm = _ConcurrencyTrackingLLM(delay=0.05)
        orchestrator = _make_orchestrator(llm, subtasks, concurrency=2)
        orchestrator.run(
            "Please compare and contrast the refund policy and the shipping policy and explain how they differ from industry standards in full detail",
            _FakeProfile(),
            None,
        )
        assert llm.max_in_flight <= 2

    def test_dependencies_respected(self):
        subtasks = [
            {"id": "t1", "query": "first", "depends_on": []},
            {"id": "t2", "query": "second", "depends_on": ["t1"]},
        ]
        llm = _ConcurrencyTrackingLLM(delay=0.01)
        orchestrator = _make_orchestrator(llm, subtasks, concurrency=4)
        orchestrator.run(
            "Please compare and contrast the refund policy and the shipping policy and explain how they differ from industry standards in full detail",
            _FakeProfile(),
            None,
        )
        # t1 must be answered before t2 starts.
        assert llm.calls.index("first") < llm.calls.index("second")

    def test_one_failure_does_not_cancel_the_batch(self):
        subtasks = [
            {"id": "t1", "query": "will fail", "depends_on": []},
            {"id": "t2", "query": "will succeed", "depends_on": []},
        ]

        class _PartiallyFailingLLM:
            def answer(self, question, context, domain_prompt):
                if "Synthesize" in domain_prompt:
                    return "final [1]"
                if question == "will fail":
                    raise RuntimeError("boom")
                return "ok"

        orchestrator = _make_orchestrator(_PartiallyFailingLLM(), subtasks)
        result = orchestrator.run(
            "Please compare and contrast the refund policy and the shipping policy and explain how they differ from industry standards in full detail",
            _FakeProfile(),
            None,
        )
        assert "t1" in result["failed"]
        assert "t2" in result["succeeded"]
