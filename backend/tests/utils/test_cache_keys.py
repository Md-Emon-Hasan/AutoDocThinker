"""Tests for the answer-cache key: app/rag/service.py::_answer_cache_key.

This is the highest-risk area in the caching work -- a cached answer
derived from private documents must never reach another scope/session,
and a stale index must never serve a post-ingest answer. One test per
key component.
"""

from app.rag.service import _answer_cache_key


def _base():
    return {
        "question": "what are the terms?",
        "mode": "advanced",
        "domain": "general",
        "index_version": 1,
        "model": "model-a",
        "scope": "session:a",
    }


class TestAnswerCacheKey:
    def test_same_inputs_same_key(self):
        assert _answer_cache_key(**_base()) == _answer_cache_key(**_base())

    def test_question_changes_key(self):
        other = _base()
        other["question"] = "different question"
        assert _answer_cache_key(**_base()) != _answer_cache_key(**other)

    def test_mode_changes_key(self):
        other = _base()
        other["mode"] = "naive"
        assert _answer_cache_key(**_base()) != _answer_cache_key(**other)

    def test_domain_changes_key(self):
        other = _base()
        other["domain"] = "legal"
        assert _answer_cache_key(**_base()) != _answer_cache_key(**other)

    def test_index_version_changes_key(self):
        other = _base()
        other["index_version"] = 2
        assert _answer_cache_key(**_base()) != _answer_cache_key(**other)

    def test_model_changes_key(self):
        other = _base()
        other["model"] = "model-b"
        assert _answer_cache_key(**_base()) != _answer_cache_key(**other)

    def test_scope_changes_key(self):
        other = _base()
        other["scope"] = "session:b"
        assert _answer_cache_key(**_base()) != _answer_cache_key(**other)

    def test_normalized_question_whitespace_and_case_insensitive(self):
        other = _base()
        other["question"] = "  WHAT are THE   terms?  "
        assert _answer_cache_key(**_base()) == _answer_cache_key(**other)
