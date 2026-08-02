"""Tests for app/orchestration/planner.py: decomposition, dependency
graph, depth/count caps, trivial queries bypass planning."""

import json

from app.orchestration.planner import Planner, is_trivial


class _StubTaskClient:
    def __init__(self, response: str) -> None:
        self._response = response
        self.calls = 0

    def answer(self, question, context, domain_prompt):
        self.calls += 1
        return self._response


class TestIsTrivial:
    def test_short_question_is_trivial(self):
        assert is_trivial("What is the refund policy?")

    def test_long_multi_part_question_is_not_trivial(self):
        long_q = (
            "Compare the refund policy and the shipping policy and explain how "
            "they differ from industry standards, then summarize the pros and cons"
        )
        assert not is_trivial(long_q)

    def test_short_but_conjunctive_question_is_not_trivial(self):
        assert not is_trivial("What is X and what is Y")


class TestPlannerTrivialBypass:
    def test_trivial_query_makes_no_llm_call(self):
        client = _StubTaskClient("unused")
        planner = Planner(client)
        subtasks, made_call = planner.plan("What is the refund policy?")
        assert made_call is False
        assert client.calls == 0
        assert len(subtasks) == 1
        assert subtasks[0].query == "What is the refund policy?"

    def test_no_task_client_falls_back_to_single_task(self):
        planner = Planner(None)
        subtasks, made_call = planner.plan("anything at all")
        assert made_call is False
        assert len(subtasks) == 1


class TestPlannerDecomposition:
    def test_decomposes_nontrivial_query(self):
        response = json.dumps(
            {
                "subtasks": [
                    {"id": "t1", "query": "sub question one", "depends_on": []},
                    {"id": "t2", "query": "sub question two", "depends_on": ["t1"]},
                ]
            }
        )
        client = _StubTaskClient(response)
        planner = Planner(client)
        long_q = "Compare X and Y and explain the differences in detail please"
        subtasks, made_call = planner.plan(long_q)
        assert made_call is True
        assert client.calls == 1
        assert len(subtasks) == 2
        assert subtasks[1].depends_on == ["t1"]

    def test_caps_subtask_count(self):
        many = [{"id": f"t{i}", "query": f"q{i}", "depends_on": []} for i in range(10)]
        client = _StubTaskClient(json.dumps({"subtasks": many}))
        planner = Planner(client, max_subtasks=3)
        long_q = "Compare X and Y and Z and explain the differences in full detail"
        subtasks, _ = planner.plan(long_q)
        assert len(subtasks) == 3

    def test_drops_dependency_on_nonexistent_id(self):
        response = json.dumps(
            {
                "subtasks": [
                    {"id": "t1", "query": "q1", "depends_on": ["ghost"]},
                ]
            }
        )
        client = _StubTaskClient(response)
        planner = Planner(client)
        long_q = "Compare X and Y and explain the differences in full detail here"
        subtasks, _ = planner.plan(long_q)
        assert subtasks[0].depends_on == []

    def test_drops_self_dependency(self):
        response = json.dumps(
            {"subtasks": [{"id": "t1", "query": "q1", "depends_on": ["t1"]}]}
        )
        client = _StubTaskClient(response)
        planner = Planner(client)
        long_q = "Compare X and Y and explain the differences in full detail please"
        subtasks, _ = planner.plan(long_q)
        assert subtasks[0].depends_on == []

    def test_malformed_json_falls_back_to_single_task(self):
        client = _StubTaskClient("not json")
        planner = Planner(client)
        long_q = "Compare X and Y and explain the differences in full detail please"
        subtasks, made_call = planner.plan(long_q)
        assert made_call is True
        assert len(subtasks) == 1

    def test_empty_subtasks_falls_back_to_single_task(self):
        client = _StubTaskClient(json.dumps({"subtasks": []}))
        planner = Planner(client)
        long_q = "Compare X and Y and explain the differences in full detail please"
        subtasks, _ = planner.plan(long_q)
        assert len(subtasks) == 1
