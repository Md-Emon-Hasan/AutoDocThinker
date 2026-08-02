"""A sub-agent cannot see full state or reach outside its scope; a
sub-agent failure must not fail the query."""

from app.orchestration.models import SubTask
from app.orchestration.subagent import SubAgent


class _FakeProfile:
    system_prompt = "system prompt"


class _RecordingRetrieval:
    """Records exactly what it was called with, so tests can assert a
    sub-agent only ever passes its OWN subtask query and metadata_filter
    -- never the full shared state or other sub-tasks' results."""

    def __init__(self, docs=None):
        self.docs = docs or []
        self.calls = []

    def retrieve(self, query, k, metadata_filter):
        self.calls.append({"query": query, "k": k, "metadata_filter": metadata_filter})
        return self.docs


class _StubLLM:
    def __init__(self, response="an answer"):
        self.response = response
        self.received_context = None
        self.received_question = None

    def answer(self, question, context, domain_prompt):
        self.received_question = question
        self.received_context = context
        return self.response


class _RaisingLLM:
    def answer(self, *args, **kwargs):
        raise RuntimeError("provider outage")


class TestSubAgentScoping:
    def test_only_receives_its_own_subtask_query(self):
        retrieval = _RecordingRetrieval()
        llm = _StubLLM()
        scope_filter = {"scope": ["shared", "session:a"]}
        agent = SubAgent(retrieval, llm, _FakeProfile(), scope_filter)
        subtask = SubTask(id="t1", query="only this sub-question", depends_on=[])

        agent.run(subtask)

        assert retrieval.calls == [
            {"query": "only this sub-question", "k": 6, "metadata_filter": scope_filter}
        ]
        assert llm.received_question == "only this sub-question"

    def test_inherits_callers_scope_filter_verbatim(self):
        retrieval = _RecordingRetrieval()
        scope_filter = {"scope": ["shared", "session:private"]}
        agent = SubAgent(retrieval, _StubLLM(), _FakeProfile(), scope_filter)
        agent.run(SubTask(id="t1", query="q", depends_on=[]))
        assert retrieval.calls[0]["metadata_filter"] is scope_filter

    def test_does_not_receive_other_subtasks_results(self):
        """SubAgent.run()'s only inputs are (subtask); there is no
        parameter through which sibling sub-task results or full
        conversation history could leak in."""
        import inspect

        signature = inspect.signature(SubAgent.run)
        assert list(signature.parameters) == ["self", "subtask"]


class TestSubAgentFailureIsolation:
    def test_llm_failure_returns_unsuccessful_result_not_raise(self):
        agent = SubAgent(_RecordingRetrieval(), _RaisingLLM(), _FakeProfile(), None)
        result = agent.run(SubTask(id="t1", query="q", depends_on=[]))
        assert result.success is False
        assert result.error is not None
        assert result.subtask_id == "t1"

    def test_retrieval_failure_returns_unsuccessful_result_not_raise(self):
        class _RaisingRetrieval:
            def retrieve(self, *a, **k):
                raise RuntimeError("index outage")

        agent = SubAgent(_RaisingRetrieval(), _StubLLM(), _FakeProfile(), None)
        result = agent.run(SubTask(id="t1", query="q", depends_on=[]))
        assert result.success is False

    def test_success_returns_answer_and_sources(self):
        agent = SubAgent(
            _RecordingRetrieval(), _StubLLM("the answer"), _FakeProfile(), None
        )
        result = agent.run(SubTask(id="t1", query="q", depends_on=[]))
        assert result.success is True
        assert result.answer == "the answer"
