"""Consolidated tests for core module: config, constants, environment, errors,
paths, cli, lifecycle, logging, exceptions, and application/dependencies."""

from app.core.config import get_config


class TestConfig:
    def test_app_name_and_version(self):
        cfg = get_config()
        assert cfg.app_name == "AutoDocThinker"
        assert cfg.version == "3.0.0"
