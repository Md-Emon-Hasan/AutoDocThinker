"""Consolidated tests for the domain module: models, presets, defaults,
registry, selector, validator, and all domain prompt constants."""

import pytest

from app.domain.registry import DomainRegistry
from app.domain.validator import validate_profile


class TestValidator:
    def test_valid_profile(self):
        profile, mode = validate_profile(DomainRegistry(), "finance", "CRAG")
        assert profile.name == "finance" and mode == "crag"

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError):
            validate_profile(DomainRegistry(), "general", "missing")
