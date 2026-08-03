"""Consolidated tests for core module: config, constants, environment, errors,
paths, cli, lifecycle, logging, exceptions, and application/dependencies."""

from app.logging_config import configure_logging


class TestLogging:
    def test_configure_logging(self):
        configure_logging("DEBUG")  # should not raise
