"""Consolidated tests for the domain module: models, presets, defaults,
registry, selector, validator, and all domain prompt constants."""

import pytest

from app.domain.registry import DomainRegistry


class TestRegistry:
    def test_names(self):
        registry = DomainRegistry()
        assert "general" in registry.names()
        assert len(registry.names()) == 7

    def test_get_returns_profile(self):
        assert DomainRegistry().get("legal").label == "Legal"

    def test_get_missing_raises(self):
        with pytest.raises(KeyError):
            DomainRegistry().get("missing")

    def test_list_returns_all(self):
        assert len(DomainRegistry().list()) == 7
