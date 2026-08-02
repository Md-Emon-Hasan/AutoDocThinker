"""Tests for app/llm/gateway/routing.py."""

import pytest

from app.core.config import RAGConfig
from app.llm.gateway.models import TaskCategory
from app.llm.gateway.routing import resolve_model


class TestResolveModel:
    def test_returns_configured_model_for_task(self):
        config = RAGConfig(task_model_map={"answer_generation": "base-model"})
        assert resolve_model(TaskCategory.ANSWER_GENERATION, config) == "base-model"

    def test_unknown_task_raises(self):
        config = RAGConfig(task_model_map={"answer_generation": "base-model"})
        with pytest.raises(KeyError):
            resolve_model(TaskCategory.VERIFICATION, config)

    def test_escalates_above_threshold_when_configured(self):
        config = RAGConfig(
            task_model_map={"answer_generation": "base-model"},
            escalated_model_map={"answer_generation": "big-model"},
            complexity_escalation_threshold=0.7,
        )
        assert (
            resolve_model(TaskCategory.ANSWER_GENERATION, config, complexity_hint=0.9)
            == "big-model"
        )

    def test_no_escalation_below_threshold(self):
        config = RAGConfig(
            task_model_map={"answer_generation": "base-model"},
            escalated_model_map={"answer_generation": "big-model"},
            complexity_escalation_threshold=0.7,
        )
        assert (
            resolve_model(TaskCategory.ANSWER_GENERATION, config, complexity_hint=0.1)
            == "base-model"
        )

    def test_escalation_is_noop_without_explicit_config(self):
        """Escalation only activates when the caller opts in with an
        entry in escalated_model_map -- otherwise, even a complexity_hint
        above threshold changes nothing, preserving today's single-model
        behavior by default."""
        config = RAGConfig(task_model_map={"answer_generation": "base-model"})
        assert (
            resolve_model(TaskCategory.ANSWER_GENERATION, config, complexity_hint=0.99)
            == "base-model"
        )
