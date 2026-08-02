"""Citation merge and dedup, all citations traceable, verification runs
once (on the synthesized answer only -- enforced at the RAGService
boundary, see app/rag/service.py's single _apply_verification call)."""

from app.orchestration.models import SubAgentResult
from app.orchestration.synthesis import synthesize


class _FakeProfile:
    system_prompt = "system prompt"


class _RecordingLLM:
    def __init__(self, answer="synthesized [1][2]"):
        self.answer_text = answer
        self.received_context = None

    def answer(self, question, context, domain_prompt):
        self.received_context = context
        return self.answer_text


class TestSynthesis:
    def test_merges_and_dedups_sources_by_chunk_id(self):
        r1 = SubAgentResult(
            subtask_id="t1",
            answer="a1",
            sources=[{"chunk_id": "c1", "source": "doc.txt"}],
            success=True,
        )
        r2 = SubAgentResult(
            subtask_id="t2",
            answer="a2",
            sources=[
                {"chunk_id": "c1", "source": "doc.txt"},  # duplicate
                {"chunk_id": "c2", "source": "doc.txt"},
            ],
            success=True,
        )
        llm = _RecordingLLM()
        result = synthesize("q", [r1, r2], llm, _FakeProfile(), skipped=[])
        assert len(result["sources"]) == 2  # c1 deduped

    def test_renumbers_sources_sequentially(self):
        r1 = SubAgentResult(
            subtask_id="t1", answer="a1", sources=[{"chunk_id": "c1"}], success=True
        )
        r2 = SubAgentResult(
            subtask_id="t2", answer="a2", sources=[{"chunk_id": "c2"}], success=True
        )
        result = synthesize("q", [r1, r2], _RecordingLLM(), _FakeProfile(), skipped=[])
        ids = [s["id"] for s in result["sources"]]
        assert ids == [1, 2]

    def test_reports_succeeded_failed_skipped(self):
        r1 = SubAgentResult(subtask_id="t1", answer="a1", sources=[], success=True)
        r2 = SubAgentResult(
            subtask_id="t2", answer="", sources=[], success=False, error="boom"
        )
        result = synthesize(
            "q", [r1, r2], _RecordingLLM(), _FakeProfile(), skipped=["t3"]
        )
        assert result["succeeded"] == ["t1"]
        assert result["failed"] == ["t2"]
        assert result["skipped"] == ["t3"]

    def test_all_failed_returns_explicit_message_without_llm_call(self):
        r1 = SubAgentResult(
            subtask_id="t1", answer="", sources=[], success=False, error="boom"
        )
        llm = _RecordingLLM()
        result = synthesize("q", [r1], llm, _FakeProfile(), skipped=[])
        assert result["succeeded"] == []
        assert "Unable" in result["answer"]
        assert llm.received_context is None  # never called

    def test_synthesis_calls_llm_exactly_once(self):
        r1 = SubAgentResult(subtask_id="t1", answer="a1", sources=[], success=True)
        r2 = SubAgentResult(subtask_id="t2", answer="a2", sources=[], success=True)

        class _CountingLLM:
            def __init__(self):
                self.calls = 0

            def answer(self, question, context, domain_prompt):
                self.calls += 1
                return "final"

        llm = _CountingLLM()
        synthesize("q", [r1, r2], llm, _FakeProfile(), skipped=[])
        assert llm.calls == 1

    def test_context_notes_failed_and_skipped_subtasks(self):
        r1 = SubAgentResult(subtask_id="t1", answer="a1", sources=[], success=True)
        r2 = SubAgentResult(
            subtask_id="t2", answer="", sources=[], success=False, error="boom"
        )
        llm = _RecordingLLM()
        synthesize("q", [r1, r2], llm, _FakeProfile(), skipped=["t3"])
        assert "t2" in llm.received_context
        assert "t3" in llm.received_context
