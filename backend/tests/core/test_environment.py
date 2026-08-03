"""Consolidated tests for core module: config, constants, environment, errors,
paths, cli, lifecycle, logging, exceptions, and application/dependencies."""

from app.core.environment import env_bool


class TestEnvironment:
    def test_env_bool_true(self, monkeypatch):
        monkeypatch.setenv("FLAG", "yes")
        assert env_bool("FLAG") is True

    def test_env_bool_default(self):
        assert env_bool("MISSING", True) is True
        assert env_bool("MISSING") is False
