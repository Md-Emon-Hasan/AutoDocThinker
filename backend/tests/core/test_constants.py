"""Consolidated tests for core module: config, constants, environment, errors,
paths, cli, lifecycle, logging, exceptions, and application/dependencies."""

from app.core.constants import (
    APP_TITLE,
    DEFAULT_DOMAIN,
    DEFAULT_RAG_MODE,
    SUPPORTED_FILE_TYPES,
)


class TestConstants:
    def test_app_title(self):
        assert APP_TITLE == "AutoDocThinker"

    def test_defaults(self):
        assert DEFAULT_DOMAIN == "general"
        assert DEFAULT_RAG_MODE == "advanced"
        assert "txt" in SUPPORTED_FILE_TYPES
