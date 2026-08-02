"""Tests for app/verification/agent.py::VerifierAgent."""

import json

from app.verification.agent import VerifierAgent
from app.verification.critic import Critic


class _StubTaskClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = 0

    def answer(self, question, context, domain_prompt):
        self.calls += 1
        response = self._responses[min(self.calls - 1, len(self._responses) - 1)]
        return response


def _sources():
    return [{"id": 1, "label": "l", "source": "s", "chunk_id": "c1"}]


class TestVerifierAgent:
    def test_structured_output_parsed(self):
        client = _StubTaskClient(
            [
                json.dumps(
                    {
                        "groundedness": 0.9,
                        "claims": [
                            {"text": "fact", "supported": True, "chunk_id": "c1"}
                        ],
                        "unsupported_claims": [],
                    }
                )
            ]
        )
        agent = VerifierAgent(task_client=client)
        result = agent.verify("q", "fact [1]", "context", _sources())
        assert result.verified is True
        assert result.groundedness == 0.9
        assert result.claims[0].supported is True

    def test_unsupported_claims_surfaced(self):
        client = _StubTaskClient(
            [
                json.dumps(
                    {
                        "groundedness": 0.2,
                        "claims": [],
                        "unsupported_claims": ["wild claim"],
                    }
                )
            ]
        )
        agent = VerifierAgent(task_client=client)
        result = agent.verify("q", "wild claim", "context", _sources())
        assert "wild claim" in result.unsupported_claims

    def test_malformed_json_retried_once_then_degrades(self):
        client = _StubTaskClient(["not json", "still not json"])
        agent = VerifierAgent(task_client=client)
        result = agent.verify("q", "answer [1]", "context", _sources())
        assert client.calls == 2
        assert result.verified is False
        assert result.groundedness is None

    def test_malformed_json_then_valid_on_retry_succeeds(self):
        client = _StubTaskClient(
            [
                "not json",
                json.dumps(
                    {"groundedness": 0.8, "claims": [], "unsupported_claims": []}
                ),
            ]
        )
        agent = VerifierAgent(task_client=client)
        result = agent.verify("q", "answer [1]", "context", _sources())
        assert client.calls == 2
        assert result.verified is True
        assert result.groundedness == 0.8

    def test_no_task_client_returns_unverified_with_mechanical_checks_only(self):
        agent = VerifierAgent(task_client=None)
        result = agent.verify("q", "answer with no citation", "context", _sources())
        assert result.verified is False
        assert result.groundedness is None
        assert any("no citations" in issue for issue in result.citation_issues)

    def test_verifier_failure_returns_answer_marked_unverified(self):
        class _RaisingClient:
            def answer(self, *args, **kwargs):
                raise RuntimeError("provider outage")

        agent = VerifierAgent(task_client=_RaisingClient())
        result = agent.verify("q", "answer [1]", "context", _sources())
        assert result.verified is False

    def test_citation_issues_always_populated_even_when_llm_succeeds(self):
        client = _StubTaskClient(
            [json.dumps({"groundedness": 0.9, "claims": [], "unsupported_claims": []})]
        )
        agent = VerifierAgent(task_client=client)
        result = agent.verify(
            "q", "uncited claim with no bracket", "context", _sources()
        )
        assert any("no citations" in issue for issue in result.citation_issues)

    def test_custom_critic_is_used(self):
        class _FakeCritic(Critic):
            def assess(self, question, answer, context, task_client):
                return {"groundedness": 0.42, "claims": [], "unsupported_claims": []}

        agent = VerifierAgent(
            task_client=_StubTaskClient(["unused"]), critic=_FakeCritic()
        )
        result = agent.verify("q", "answer [1]", "context", _sources())
        assert result.groundedness == 0.42
