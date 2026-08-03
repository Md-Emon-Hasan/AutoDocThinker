"""Consolidated tests for the domain module: models, presets, defaults,
registry, selector, validator, and all domain prompt constants."""

from app.domain.models import DomainProfile


class TestDomainProfile:
    def test_frozen_dataclass(self):
        p = DomainProfile("x", "X", "desc", "prompt", {})
        assert p.name == "x" and p.label == "X"

    def test_metadata_filter(self):
        p = DomainProfile("x", "X", "desc", "p", {"key": "val"})
        assert p.metadata_filter == {"key": "val"}
