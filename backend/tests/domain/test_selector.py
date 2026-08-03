"""Consolidated tests for the domain module: models, presets, defaults,
registry, selector, validator, and all domain prompt constants."""

from app.domain.registry import DomainRegistry
from app.domain.selector import select_profile


class TestSelector:
    def test_returns_domain_and_mode(self):
        result = select_profile(DomainRegistry(), "technical", "self_rag")
        assert result["domain"] == "technical"
        assert result["rag_mode"] == "self_rag"
        assert result["prompt"]
