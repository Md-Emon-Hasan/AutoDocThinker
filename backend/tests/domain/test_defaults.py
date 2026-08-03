"""Consolidated tests for the domain module: models, presets, defaults,
registry, selector, validator, and all domain prompt constants."""

from app.domain.defaults import build_domain_presets


class TestDefaults:
    def test_build_has_seven_entries(self):
        presets = build_domain_presets()
        assert len(presets) == 7

    def test_all_keys_present(self):
        names = set(build_domain_presets())
        expected = {
            "general",
            "legal",
            "medical",
            "finance",
            "education",
            "technical",
            "customer_support",
        }
        assert names == expected
