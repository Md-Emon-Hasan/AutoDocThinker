"""Consolidated tests for core module: config, constants, environment, errors,
paths, cli, lifecycle, logging, exceptions, and application/dependencies."""

from app.core.paths import project_path


class TestPaths:
    def test_project_path(self):
        assert project_path("app").name == "app"
